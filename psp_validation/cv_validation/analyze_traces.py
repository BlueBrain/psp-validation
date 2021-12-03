"""
Loads traces from HDF5 dump, adds OU noise, extract peak PSP amplitudes and calculates CV of them
see Barros-Zulaica et al 2019; last modified: András Ecker, 06.2021
"""

import os
import logging
import multiprocessing
from functools import partial

import h5py
import numpy as np
from efel import getFeatureValues
from tqdm import tqdm

from psp_validation.cv_validation.OU_generator import add_ou_noise


SPIKE_TH = -30  # (mV) NEURON's built in spike threshold
L = logging.getLogger(__name__)


def _load_traces(h5f):
    """Loads in traces from custom HDF5 dump and returns ndarray with 1 row per seed (aka. trial)
    TODO: after outputting them in the same format as `psp-validation` does adapt the loader"""
    seeds = list(h5f)
    t = h5f[seeds[0]]["time"][:]
    traces = np.empty((len(seeds), len(t)), dtype=np.float32)

    for i, seed in enumerate(seeds):
        traces[i, :] = h5f[seed]["soma"][:]

    return t, traces


def _filter_traces(t, traces, t_stim):
    """Filters out spiking trials. (Similar to `psp-validation`'s SpikeFilter class)"""
    # spikes in the beginning are OK, but not after the stimulus [t > t_stim]
    non_spiking_traces = traces[np.all(traces[:, t > t_stim], axis=1)]
    return non_spiking_traces if non_spiking_traces.size > 0 else None


def get_noisy_traces(h5f, protocol):
    """Loads in traces, filters out the spiking ones and adds OU noise to them"""
    t, traces = _load_traces(h5f)
    np.random.seed(h5f.attrs['base_seed'])
    t_stim = protocol['t_stim']
    filtered_traces = _filter_traces(t, traces, t_stim)

    if filtered_traces is None:
        return t, None

    tau = protocol['tau']
    sigma = protocol['sigma']
    noisy_traces = add_ou_noise(t, filtered_traces, tau, sigma)

    return t, noisy_traces


def _get_cvs_and_jk_cvs_worker(pre_post_syn_type, h5_path, protocol):
    """Worker function for getting the CVs and JK CVs for given pair."""
    bad_pair = cv = jk_cv = None
    min_trials = protocol['min_good_trials']
    t_stim = protocol['t_stim']
    pre, post, syn_type = pre_post_syn_type
    pair = f'{pre}_{post}'

    with h5py.File(h5_path, 'r') as h5:
        t, noisy_traces = get_noisy_traces(h5[pair], protocol)

    if noisy_traces is not None and noisy_traces.shape[0] >= min_trials:
        cv = calc_cv(t, noisy_traces, syn_type, t_stim, jk=False)
        jk_cv = calc_cv(t, noisy_traces, syn_type, t_stim, jk=True)
    else:
        bad_pair = pair

    return cv, jk_cv, bad_pair


def get_cvs_and_jk_cvs(pairs, h5_path, protocol, jobs=70):
    """Gets the CVs and Jackknife sampled CVs of the psp amplitudes for given pairs."""

    func = partial(_get_cvs_and_jk_cvs_worker,
                   h5_path=h5_path,
                   protocol=protocol)

    pre_post_syn_type = pairs[['pre', 'post', 'synapse_type']].itertuples(index=False, name=None)

    with multiprocessing.Pool(jobs, maxtasksperchild=1) as pool:
        res = pool.map(func, pre_post_syn_type, chunksize=1)

    return [[value for value in group if value is not None] for group in zip(*res)]


def _efel_traces(t, traces, t_stim):
    """Gets traces in the format expected by efel.getFeatureValues

    Compared to `psp-validation`'s `efel_traces` this is trial-by-trial,
    not working with the mean trace"""
    return [{"T": t, "V": trial, "stim_start": [t_stim], "stim_end": [t[-1]]} for trial in traces]


def _get_peak_amplitudes(t, traces, syn_type, t_stim):
    """Gets peak PSP amplitudes for all trials using efel.

    Similar to `psp-validation`'s `get_peak_amplitudes`"""
    assert syn_type in ["EXC", "INH"], f"unknown syn_type: {syn_type} (expected: 'EXC' or 'INH')"
    traces = _efel_traces(t, traces, t_stim)
    peak = "maximum_voltage" if syn_type == "EXC" else "minimum_voltage"
    traces_results = getFeatureValues(traces, ["voltage_base", peak])
    amplitudes = np.abs([trial[peak][0] - trial["voltage_base"][0] for trial in traces_results])
    return amplitudes


def _get_jackknife_traces(traces):
    """Performs 0-axis-wise Jackknife resampling for input array"""
    return np.vstack([np.mean(np.delete(traces, i, 0), axis=0) for i in range(traces.shape[0])])


def calc_cv(t, noisy_traces, syn_type, t_stim, jk):
    """Calculates CV (coefficient of variation std/mean) of PSPs.

    Optionally done with Jackknife resampling which averages noise and gets an unbiased
    estimate of the std."""
    if jk:
        jk_traces = _get_jackknife_traces(noisy_traces)
        amplitudes = _get_peak_amplitudes(t, jk_traces, syn_type, t_stim)

        n = len(amplitudes)
        mean_amplitude = np.mean(amplitudes)

        # Since JK variance is Var = (N-1)/N * [SUM_OF_SQUARED_DIFF], we can't use np.std()
        jk_std = np.sqrt((n - 1) / n * np.sum((amplitudes - mean_amplitude)**2))
        return jk_std / mean_amplitude
    else:
        amplitudes = _get_peak_amplitudes(t, noisy_traces, syn_type, t_stim)
        return np.std(amplitudes) / np.mean(amplitudes)


def get_all_cvs(pathway, out_dir, pairs, nrrp, protocol):
    """Calculates CVs w/ and w/o Jackknife resampling for all pairs and all NRRP values"""
    sims_dir = os.path.join(out_dir, "simulations")
    all_cvs = {}
    n_bad_pairs = 0

    for nrrp_ in tqdm(range(nrrp[0], nrrp[1] + 1), desc="Iterating over NRRP"):
        h5_path = os.path.join(sims_dir, f"simulation_nrrp{nrrp_}.h5")

        cvs, jk_cvs, bad_pairs = get_cvs_and_jk_cvs(pairs,
                                                    h5_path,
                                                    protocol)
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
