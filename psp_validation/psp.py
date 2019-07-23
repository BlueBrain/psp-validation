"""
Check the amplitude of the compound *E*PSP; works only with excitatory
synapses at this time. However, no checks are done to see if you actually
specified an excitatory synapse. Be carefull.
Minis are not used because they provide too much noise.
No current injection other than the current to achieve the holding potential
are included. (no HypAmp for instance)
"""
import os

import bluepy
import h5py
import numpy as np

import efel
from psp_validation import get_logger
from psp_validation.pathways import get_pairs, get_synapse_type
from psp_validation.persistencyutils import dump_pair_traces
from psp_validation.utils import load_config, load_yaml

LOGGER = get_logger('lib')


def calculate_amplitude(traces,
                        syn_type,
                        trace_filter,
                        t_stim):
    """Calculate the peak amplitude for a set of simulated PSP traces.

    Applies some filtering to simulated trace set, estimates the
    element-wise mean over the set, and returns the peak amplitude.
    Returns nan if filtering removes all traces.
    """

    v, t, _, _ = mean_pair_voltage_from_traces(traces, trace_filter)

    # catch case where all traces were filtered due to spiking
    if v is None:
        LOGGER.info("calculate_amplitude: removed from avg due to spiking")
        return np.nan

    return get_peak_amplitude(t, v, t_stim, syn_type)


class SpikeFilter(object):
    """Functor to filter traces with spikes
    """

    def __init__(self, t_start, v_max):

        self.t0 = t_start
        self.v_max = v_max

    def __call__(self, traces):

        vs_filtered = []
        t = []
        for trace_ in traces:
            v_, t_ = trace_[0], trace_[1]
            if (v_ is None or get_peak_voltage(t_, v_, self.t0, 'EXC') > self.v_max):
                continue
            else:
                vs_filtered.append(v_)
                t = t_

        return vs_filtered, t


def default_spike_filter(t_start):
    """Return a SpikeFilter instance configured with t_start, v_max = -20
    """
    v_max = -20
    return SpikeFilter(t_start, v_max)


def unzip_traces(traces):
    """ Unzip a tuple of pairs into two lists
    This can be used as a "do nothing" trace filter.
    """
    data = tuple(zip(*traces))
    return list(data[0]), list(data[1])


def mean_pair_voltage_from_traces(vts,
                                  trace_filter=unzip_traces,
                                  v_clamp=None):
    """ Perform some filtering and calculate mean V over repetitions
    """

    vs, time = trace_filter(vts)
    if len(vs) == 0:
        return None, None, [], None

    # calc element-wise mean v (over reps)
    v_mean = np.mean(vs, axis=0)

    if v_clamp:
        currents = [x[2] for x in vts]
        return v_mean, time, vs, currents

    return v_mean, time, vs, None


def get_peak_voltage(time, voltage, t_stim, syn_type):
    """Return the peak voltage after time t_stim.

    Parameters:
    time: numpy.ndarray containing time measurements
    voltage: numpy.ndarray containing voltage measurements
    t_stim: numeric scalar representing stimulation time.
            Times lower than this are ignored.
    syn_type: string containing synapse type ("EXC" or "INH")

    Return:
    max value of voltage if synapse_type is "EXC" and the min otherwise.
    Both quantities are calculated for elements with time > t_stim.

    Remarks:
    Raises ValueError if either of time or voltage is an iterable
            other than a numpy.ndarray. This is because this situation
            could result in silently returning the wrong value.
    """
    _check_numpy_ndarrays(time, voltage)
    if syn_type not in {'EXC', 'INH'}:
        raise AttributeError('syn_type must be one of EXC or INH, not: {}'.format(syn_type))
    fun = np.max if syn_type == "EXC" else np.min
    return fun(voltage[time > t_stim])


def get_peak_amplitude(time, voltage, t_stim, syn_type):
    """Get the peak amplitude in a time series.

    Parameters:
    t: array holding N time measurements
    v: array holding N voltage measurements
    t_start: lower t bound for mean v calculation
    t_stim:  upper t bound for mean v calculation,
    lower t bound for peak v calculation

    Return:
    RMS of the diffetence between calculated mean v and peak v
    """
    if syn_type not in {'EXC', 'INH'}:
        raise AttributeError('syn_type must be one of EXC or INH, not: {}'.format(syn_type))

    traces = [{
        'T': time,
        'V': voltage,
        'stim_start': [t_stim],
        'stim_end': [np.max(time)],
    }]
    peak = 'maximum_voltage' if syn_type == 'EXC' else 'minimum_voltage'
    traces_results = efel.getFeatureValues(traces, [peak, 'voltage_base'])
    amplitude = abs(traces_results[0][peak][0] - traces_results[0]['voltage_base'][0])
    return amplitude


def _check_numpy_ndarrays(*args):
    """Check that all args are numpy.ndarrays.

    Checks if all of the arguments are instances of numpy.ndarray,
    raises ValueError otherwise
    """
    for arg in args:
        if not isinstance(arg, np.ndarray):
            raise ValueError("Argument must be numpy.ndarray")


def compute_scaling(psp1, psp2, v_holding, syn_type):
    """ Compute conductance scaling factor. """
    if syn_type not in {'EXC', 'INH'}:
        raise AttributeError('syn_type must be one of EXC or INH, not: {}'.format(syn_type))

    E_rev = {
        'EXC': 0.0,
        'INH': -80.0,
    }[syn_type]

    d = np.abs(E_rev - v_holding)
    return (psp2 * (1 - (psp1 / d))) / (psp1 * (1 - (psp2 / d)))


def _import_run_pair_simulation_suite():
    '''Return run_pair_simulation_suite but can also easily be mocked'''
    from psp_validation.simulation import run_pair_simulation_suite
    return run_pair_simulation_suite


def run(
    pathway_files, blueconfig, targets, output_dir, num_pairs, num_trials,
    clamp='current', dump_traces=False, dump_amplitudes=False, seed=None, jobs=None
):
    """ Obtain PSP amplitudes; derive scaling factors """
    # TODO: `pylint` is likely right about "too many everything"
    # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
    run_pair_simulation_suite = _import_run_pair_simulation_suite()

    if clamp == 'voltage':
        if dump_amplitudes:
            LOGGER.warning("Voltage clamp mode; ignoring '--dump-amplitudes' flag")
            dump_amplitudes = False

    np.random.seed(seed)

    circuit = bluepy.Circuit(blueconfig).v2
    targets = load_yaml(targets)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for config_path in pathway_files:
        title, config = load_config(config_path)
        LOGGER.info("Processing '%s' pathway...", title)

        pathway = config['pathway']
        projection = pathway.get('projection')
        if 'pairs' in pathway:
            for item in pathway['pairs']:
                assert isinstance(item, list) and len(item) == 2
            pairs = pathway['pairs']
        else:
            LOGGER.info("Querying pathway pairs...")

            def get_target(name):
                return targets.get(name, name)

            pre = get_target(pathway['pre'])
            post = get_target(pathway['post'])
            pairs = get_pairs(
                circuit, pre, post, num_pairs,
                constraints=pathway.get('constraints'),
                projection=projection
            )

        if projection is None:
            pre_syn_type = get_synapse_type(circuit, [p[0] for p in pairs])
        else:
            pre_syn_type = "EXC"

        min_ampl = config.get('min_amplitude', 0.0)

        protocol = config['protocol']
        if 'hold_I' in protocol:
            LOGGER.warning(
                "`hold_I` parameter in protocol is deprecated and will be ignored; "
                "please remove it from '%s' pathway config",
                config_path
            )
            del protocol['hold_I']
        if 'v_clamp' in protocol:
            LOGGER.warning(
                "`v_clamp` parameter in protocol is deprecated and will be ignored; "
                "please remove it from '%s' pathway config.\n"
                "For emulating voltage clamp, pass `--clamp voltage` to `psp run`.",
                config_path
            )
            del protocol['v_clamp']

        t_stim = config['protocol']['t_stim']
        if isinstance(t_stim, list):
            # in case of input spike train, use first spike time as split point
            t_stim = min(t_stim)

        t_start = t_stim - 10.
        spike_filter = default_spike_filter(t_start)

        if dump_traces:
            traces_path = os.path.join(output_dir, title + ".traces.h5")
            # create empty H5 dump or overwrite existing one
            with h5py.File(traces_path, 'w') as h5f:
                h5f.attrs['version'] = u'1.1'
                # we store voltage traces for current clamp and vice-versa
                h5f.attrs['data'] = {
                    'current': 'voltage',
                    'voltage': 'current',
                }[clamp]

        all_amplitudes = []
        for pre_gid, post_gid in pairs:
            traces = run_pair_simulation_suite(
                blueconfig, pre_gid, post_gid,
                base_seed=seed,
                n_trials=num_trials,
                n_jobs=jobs,
                clamp=clamp,
                projection=projection,
                **protocol
            )

            if clamp == 'current':
                v_mean, t, v_used, _ = mean_pair_voltage_from_traces(traces, spike_filter)
                if len(v_used) < len(traces):
                    filtered_count = len(traces) - len(v_used)
                    LOGGER.warning(
                        "%d out of %d traces filtered out for a%d-a%d simulation(s) due to spiking",
                        filtered_count, len(traces),
                        pre_gid, post_gid
                    )
                if v_mean is None:
                    LOGGER.warning(
                        "Could not extract PSP amplitude for a%d-a%d pair due to spiking",
                        pre_gid, post_gid
                    )
                    average = None
                    ampl = np.nan
                else:
                    average = np.stack([v_mean, t])
                    ampl = get_peak_amplitude(t, v_mean, t_stim, pre_syn_type)
                    if ampl < min_ampl:
                        LOGGER.warning(
                            "PSP amplitude below given threshold for a%d-a%d pair (%.3g < %.3g)",
                            pre_gid, post_gid,
                            ampl, min_ampl
                        )
                        ampl = np.nan
                all_amplitudes.append(ampl)
            else:
                average = np.mean(traces, axis=0)

            if dump_traces:
                with h5py.File(traces_path, 'a') as h5f:
                    dump_pair_traces(h5f, traces, average, pre_gid, post_gid)

        if clamp != 'current':
            continue

        if dump_amplitudes:
            amplitudes_path = os.path.join(output_dir, title + ".amplitudes.txt")
            np.savetxt(amplitudes_path, all_amplitudes, fmt="%.9f")

        model_mean = np.nanmean(all_amplitudes)
        model_std = np.nanstd(all_amplitudes)

        if 'reference' in config:
            reference = config['reference']['psp_amplitude']
            v_holding = config['protocol']['hold_V']

            if v_holding is None:
                traces_results = efel.getFeatureValues(traces, ['voltage_base'])
                v_holding = traces_results[0]['voltage_base'][0]

            scaling = compute_scaling(model_mean, reference['mean'], v_holding, pre_syn_type)
        else:
            reference = None
            scaling = None

        summary_path = os.path.join(output_dir, title + ".summary.yaml")
        with open(summary_path, 'w') as f:
            f.write("pathway: {}\n".format(title))
            f.write("model:\n")
            f.write("    mean: {}\n".format(model_mean))
            f.write("    std: {}\n".format(model_std))
            if reference is not None:
                f.write("reference:\n")
                f.write("    mean: {}\n".format(reference['mean']))
                f.write("    std: {}\n".format(reference['std']))
            if scaling is not None:
                f.write("scaling: {}\n".format(scaling))
