"""
Loads traces from HDF5 dump, adds OU noise, extract peak PSP amplitudes and calculates CV of them
see Barros-Zulaica et al 2019; last modified: András Ecker, 06.2021
"""

import os
import logging

import h5py
import joblib
import numpy as np
from efel import getFeatureValues
from tqdm import tqdm

from psp_validation.cv_validation.OU_generator import add_ou_noise
from psp_validation.features import check_syn_type, efel_traces, get_peak_amplitudes


SPIKE_TH = -30  # (mV) NEURON's built in spike threshold
L = logging.getLogger(__name__)


def _load_traces(h5f, clamp):
    """Loads in traces from custom HDF5 dump and returns ndarray with 1 row per seed (aka. trial)
    TODO: after outputting them in the same format as `psp-validation` does adapt the loader"""
    seeds = list(h5f)
    t = h5f[seeds[0]]["time"][:]
    traces = np.empty((len(seeds), len(t)), dtype=np.float32)

    trace_key = 'soma_current' if clamp == 'voltage' else 'soma_voltage'

    for i, seed in enumerate(seeds):
        traces[i, :] = h5f[seed][trace_key][:]

    return t, traces


def _filter_traces(t, traces, t_stim):
    """Filters out spiking trials. (Similar to `psp-validation`'s SpikeFilter class)"""
    # spikes in the beginning are OK, but not after the stimulus [t > t_stim]
    non_spiking_traces = traces[np.all(traces[:, t > t_stim] <= SPIKE_TH, axis=1)]
    return non_spiking_traces if non_spiking_traces.size > 0 else None


def get_noisy_traces(h5f, protocol, clamp):
    """Loads in traces, filters out the spiking ones and adds OU noise to them"""
    t, traces = _load_traces(h5f, clamp)
    np.random.seed(h5f.attrs['base_seed'])
    t_stim = protocol['t_stim']
    filtered_traces = _filter_traces(t, traces, t_stim) if clamp == 'current' else traces

    if filtered_traces is None:
        return t, None

    tau = protocol['tau']
    sigma = protocol['sigma']
    noisy_traces = add_ou_noise(t, filtered_traces, tau, sigma)

    return t, noisy_traces


def _get_cvs_and_jk_cvs_worker(pre_post_syn_type, h5_path, protocol):
    """Worker function for getting the CVs and JK CVs for given pair."""
    bad_pair = cv = jk_cv = None
    pre, post, syn_type = pre_post_syn_type
    pair = f'{pre}_{post}'

    with h5py.File(h5_path, 'r') as h5:
        clamp = h5.attrs.get('clamp')
        t, noisy_traces = get_noisy_traces(h5[pair], protocol, clamp)

    if noisy_traces is not None and noisy_traces.shape[0] >= protocol['min_good_trials']:
        cv = calc_cv(t, noisy_traces, syn_type, protocol['t_stim'], clamp, jk=False)
        jk_cv = calc_cv(t, noisy_traces, syn_type, protocol['t_stim'], clamp, jk=True)
    else:
        bad_pair = pair

    return cv, jk_cv, bad_pair


def get_cvs_and_jk_cvs(pairs, h5_path, protocol, n_jobs=None):
    """Gets the CVs and Jackknife sampled CVs of the psp amplitudes for given pairs."""

    pre_post_syn_type = pairs[['pre', 'post', 'synapse_type']].itertuples(index=False, name=None)

    if n_jobs is None:
        n_jobs = 1
    elif n_jobs <= 0:
        n_jobs = -1

    worker = joblib.delayed(_get_cvs_and_jk_cvs_worker)
    results = joblib.Parallel(n_jobs=n_jobs, backend='loky')([
        worker(
            pre_post_syn_type=sample,
            h5_path=h5_path,
            protocol=protocol,
        )
        for sample in pre_post_syn_type
    ])

    return [[value for value in group if value is not None] for group in zip(*results)]


def _get_peak_amplitudes_current(t, trace, t_stim, syn_type):
    """Gets the peak PSC amplitudes for trials using efel.

    Similar to `psp-validation`'s `get_peak_amplitudes`"""
    check_syn_type(syn_type)
    # There is no {minimum,maximum}_current in efel, so exploiting voltage here
    # efel "should" be ignorant about it.
    traces = efel_traces(t, trace, t_stim)
    peak = 'minimum_voltage' if syn_type == 'EXC' else 'maximum_voltage'
    feature_values = getFeatureValues(traces, ['voltage_base', peak])[0]
    return np.abs(feature_values[peak] - feature_values['voltage_base'])


def _get_peak_amplitudes(t, traces, t_stim, syn_type, clamp):
    """Gets peak PSC/PSP amplitudes for all trials."""
    t = np.tile(t, (len(traces), 1))

    func = get_peak_amplitudes if clamp == 'current' else _get_peak_amplitudes_current
    return func(t, traces, t_stim, syn_type)


def _get_jackknife_traces(traces):
    """Performs 0-axis-wise Jackknife resampling for input array"""
    return np.vstack([np.mean(np.delete(traces, i, 0), axis=0) for i in range(traces.shape[0])])


def calc_cv(t, noisy_traces, syn_type, t_stim, clamp, jk):
    """Calculates CV (coefficient of variation std/mean) of PSPs.

    Optionally done with Jackknife resampling which averages noise and gets an unbiased
    estimate of the std."""

    if jk:
        jk_traces = _get_jackknife_traces(noisy_traces)
        amplitudes = _get_peak_amplitudes(t, jk_traces, t_stim, syn_type, clamp)

        n = len(amplitudes)
        mean_amplitude = np.mean(amplitudes)

        # Since JK variance is Var = (N-1)/N * [SUM_OF_SQUARED_DIFF], we can't use np.std()
        jk_std = np.sqrt((n - 1) / n * np.sum((amplitudes - mean_amplitude)**2))
        return jk_std / mean_amplitude
    else:
        amplitudes = _get_peak_amplitudes(t, noisy_traces, t_stim, syn_type, clamp)
        return np.std(amplitudes) / np.mean(amplitudes)


def get_all_cvs(pathway, out_dir, pairs, nrrp, protocol, n_jobs=None):
    """Calculates CVs w/ and w/o Jackknife resampling for all pairs and all NRRP values"""
    sims_dir = os.path.join(out_dir, "simulations")
    all_cvs = {}
    n_bad_pairs = 0

    for nrrp_ in tqdm(range(nrrp[0], nrrp[1] + 1), desc="Iterating over NRRP"):
        h5_path = os.path.join(sims_dir, f"simulation_nrrp{nrrp_}.h5")

        cvs, jk_cvs, bad_pairs = get_cvs_and_jk_cvs(pairs,
                                                    h5_path,
                                                    protocol,
                                                    n_jobs=n_jobs)
        all_cvs[f"nrrp{nrrp_}"] = {"CV": np.asarray(cvs),
                                   "JK_CV": np.asarray(jk_cvs)}
        if bad_pairs:
            n_bad_pairs += len(bad_pairs)
            L.debug("%s NRRP:%i following pairs cannot be analyzed due to spiking: \n\t%s",
                    pathway, nrrp_, "\n\t".join(bad_pairs))

    if n_bad_pairs > 0:
        L.info("For the %s pathway %i sims couldn't be analyzed due to spiking",
               pathway, n_bad_pairs)

    return all_cvs
