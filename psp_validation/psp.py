"""
Check the amplitude of the compound *E*PSP; works only with excitatory
synapses at this time. However, no checks are done to see if you actually
specified an excitatory synapse. Be carefull.
Minis are not used because they provide too much noise.
No current injection other than the current to achieve the holding potential
are included. (no HypAmp for instance)
"""

#pylint: skip-file

import numpy as np
import bluepy
import collections
import multiprocessing
import sys
import traceback
import logging


LOGGER = logging.getLogger(__name__)


def calculate_amplitude(traces,
                        syn_type,
                        trace_filter,
                        t_stim):
    """Calculate the peak amplitude for a set of simulated PSP traces.

    Applies some filtering to simulated trace set, estimates the
    element-wise mean over the set, and returns the peak amplitude.
    Returns nan if filtering removes all traces.
    """

    v, t, vs, curr = mean_pair_voltage_from_traces(traces, trace_filter)

    # catch case where all traces were filtered due to spiking
    if v is None:
        LOGGER.info("calculate_amplitude: removed from avg due to spiking")
        return np.nan

    t_start = t_stim - 10
    return get_peak_amplitude(t, v, t_start, t_stim, syn_type)


def ensure_list(v):
    """ Convert iterable / wrap scalar into list. """
    if isinstance(v, collections.Iterable):
        return list(v)
    else:
        return [v]


def sim_pair(blue_config, pre_gid, post_gid, hold_I, t_sim, hold_V,
             t_stim, g_factor, record_dt, base_seed,
             post_ttx, v_clamp, projection):
    """ returns voltage trace for post_gid for evoking pre_spike_times \
            for synapses from pre_gid->post_gid

    pre_spike_times is float (single spike) or list

    """
    if not np.isclose(g_factor, 1.0):
        raise NotImplementedError

    import bglibpy

    LOGGER.debug('sim_pair params: %s', locals())
    LOGGER.info('sim_pair: pre_gid=%d, post_gid=%d, seed=%d', pre_gid, post_gid, base_seed)

    ssim = bglibpy.ssim.SSim(blue_config, record_dt=record_dt, base_seed=base_seed)
    ssim.instantiate_gids(
        [post_gid],
        add_replay=False,
        add_minis=False,
        add_stimuli=False,
        add_synapses=True,
        pre_spike_trains={pre_gid: ensure_list(t_stim)},
        intersect_pre_gids=[pre_gid],
        projection=projection
    )
    post_cell = ssim.cells[post_gid]

    if post_ttx:
        post_cell.enable_ttx()

    # add the current to reach the holding potential
    if hold_I is not None:
        post_cell.add_ramp(0, 10000, hold_I, hold_I, dt=0.025)

    if v_clamp:
        from neuron import h
        post_cell.addVClamp(t_sim, v_clamp)
        # manually add recording for vclamp so it has a sane name.
        v_clamp_object = post_cell.persistent[-1]
        recording = h.Vector()
        recording.record(v_clamp_object._ref_i, record_dt)
        post_cell.recordings["v_clamp"] = recording

    run_args = {}
    if hold_V is not None:
        run_args['v_init'] = hold_V
    ssim.run(t_stop=t_sim, dt=0.025, **run_args)

    t = post_cell.get_time()
    v = post_cell.get_soma_voltage()

    if v_clamp:
        i = post_cell.get_recording("v_clamp")
        return v, t, i

    LOGGER.info(
        'sim_pair: finished run for pre_gid=%d, post_gid=%d, seed=%d', pre_gid, post_gid, base_seed
    )
    return v, t, (pre_gid, post_gid)


def mp_sim_pair(all_args):
    """Forward all_args to sim_pair. Inside a try block. \
            To fix a bug, apparently.
    """
    args, kwargs = all_args
    # catch all exceptions:
    try:
        return sim_pair(*args, **kwargs)
    except:
        LOGGER.error("mp_sim_pair: caught Exception for pre_gid=%d, post_gid=%d", args[1], args[2])
        raise Exception("".join(traceback.format_exception(*sys.exc_info())))


def run_pair_trace_simulations(blue_config,
                               pre_gid,
                               post_gid,
                               hold_I,
                               hold_V,
                               t_stim,
                               t_stop,
                               g_factor,
                               record_dt,
                               post_ttx,
                               spikes,
                               v_clamp,
                               repetitions,
                               rndm_seed,
                               projection=None,
                               jobs=None):
    """Launch a series of simulations of PSP traces
    """
    LOGGER.debug('run_pair_trace_simulations params: %s', locals())
    LOGGER.info(
        'run_pair_trace_simulations: pre_gid=%d, post_gid=%d, repetitions=%d',
        pre_gid, post_gid, repetitions
    )

    if spikes is None:
        spikes = [t_stim]

    run_args = [((blue_config, pre_gid, post_gid, hold_I, t_stop),
                 dict(hold_V=hold_V, t_stim=spikes,
                      g_factor=g_factor, record_dt=record_dt,
                      base_seed=base_seed + rndm_seed,
                      post_ttx=post_ttx,
                      v_clamp=v_clamp,
                      projection=projection))
                 for base_seed in range(repetitions)[::-1]]

    LOGGER.debug('run_pair_trace_simulations run_args: %s', run_args)
    if jobs is None:
        return map(mp_sim_pair, run_args)
    else:
        max_jobs = multiprocessing.cpu_count()
        if jobs <= 0:
            jobs = max_jobs
        else:
            # spawning too many jobs would be inefficient
            jobs = min(jobs, max_jobs)
        # no need to spawn more jobs than tasks to run
        jobs = min(jobs, repetitions)
        pool = multiprocessing.Pool(jobs)
        res = pool.map(mp_sim_pair, run_args)
        pool.close()
        return res


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
            if (v_ is None or
                  get_peak_voltage(t_, v_, self.t0, 'EXC') > self.v_max):
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
    data = zip(*traces)
    return list(data[0]), list(data[1])


def mean_pair_voltage_from_traces(vts,
                                  trace_filter=unzip_traces,
                                  v_clamp=None):
    """ Perform some filtering and calculate mean V over repetitions
    """

    vs, time = trace_filter(vts)
    if len(vs) == 0:
        return None, None, None, None

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
    fun = np.max if syn_type == "EXC" else np.min
    return fun(voltage[time > t_stim])


def get_mean_voltage(time, voltage, t_start, t_stop):
    """Get the mean voltage in time range t_start to t_stop

    Parameters:
    time: numpy.ndarray containing time measurements
    voltage: numpy.ndarray containing voltage measurements
    t_start: numeric scalar representing start time
    t_stop: numeric scalar representing stop time

    Return:
    mean value of voltage calculated for time between t_start and t_stop

    Remarks:
    Raises ValueError if either of time or voltage is an iterable
            other than a numpy.ndarray. This is because this situation
            could result in silently returning the wrong value.

    """
    _check_numpy_ndarrays(time, voltage)
    return np.mean(voltage[(time > t_start) & (time < t_stop)])


def get_peak_amplitude(time, voltage, t_start, t_stim, syn_type):
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
    base_v = get_mean_voltage(time, voltage, t_start, t_stim)
    peak_v = get_peak_voltage(time, voltage, t_stim, syn_type)
    return np.sqrt((base_v - peak_v) ** 2)


def _check_numpy_ndarrays(*args):
    """Check that all args are numpy.ndarrays.

    Checks if all of the arguments are instances of numpy.ndarray,
    raises ValueError otherwise
    """
    for arg in args:
        if not isinstance(arg, np.ndarray):
            raise ValueError("Argument must be numpy.ndarray")


def compute_scaling(psp1, psp2, v_holding, syn_type):
    E_rev = {
        'EXC': 0.0,
        'INH': -80.0,
    }[syn_type]
    d = np.abs(E_rev - v_holding)
    return (psp2 * (1 - (psp1 / d))) / (psp1 * (1 - (psp2 / d)))
