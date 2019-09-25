'''The module all features extraction are defined'''
import numpy as np
from bluepy.v2.enums import Cell
import efel

from psp_validation import PSPError


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
            vs_filtered.append(v_)
            t = t_

        return vs_filtered, t


def _check_syn_type(syn_type):
    if syn_type not in {'EXC', 'INH'}:
        raise AttributeError('syn_type must be one of EXC or INH, not: {}'.format(syn_type))


def default_spike_filter(t_start):
    """Return a SpikeFilter instance configured with t_start, v_max = -20
    """
    v_max = -20
    return SpikeFilter(t_start, v_max)


def old_school_trace(simu_results):
    '''Get the traces as it was before'''
    return np.array([(voltage_array, simu_results.time) for voltage_array in
                     simu_results.voltages])


def mean_pair_voltage_from_traces(simu_results, trace_filter,
                                  v_clamp=None):
    """ Perform some filtering and calculate mean V over repetitions
    """
    vts = old_school_trace(simu_results)

    vs, time = trace_filter(vts)
    if len(vs) == 0:
        return None, None, [], None

    # calc element-wise mean v (over reps)
    v_mean = np.mean(vs, axis=0)

    currents = [x[2] for x in vts] if v_clamp else None

    return v_mean, time, vs, currents


def _check_numpy_ndarrays(*args):
    """Check that all args are numpy.ndarrays.

    Checks if all of the arguments are instances of numpy.ndarray,
    raises ValueError otherwise
    """
    for arg in args:
        if not isinstance(arg, np.ndarray):
            raise ValueError("Argument must be numpy.ndarray")


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
    _check_syn_type(syn_type)
    fun = np.max if syn_type == "EXC" else np.min
    return fun(voltage[time > t_stim])


def efel_traces(time, voltage, t_stim):
    '''Get traces in the format expected by efel.getFeatureValues'''
    return [{
        'T': time,
        'V': voltage,
        'stim_start': [t_stim],
        'stim_end': [np.max(time)],
    }]


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
    _check_syn_type(syn_type)

    traces = efel_traces(time, voltage, t_stim)
    peak = 'maximum_voltage' if syn_type == 'EXC' else 'minimum_voltage'
    traces_results = efel.getFeatureValues(traces, [peak, 'voltage_base'])
    amplitude = abs(traces_results[0][peak][0] - traces_results[0]['voltage_base'][0])
    return amplitude


def resting_potential(time, voltage, t_start, t_stim):
    '''Returns the resting potential
    '''

    traces = [{
        'T': time,
        'V': voltage,
        'stim_start': [t_start],
        'stim_end': [t_stim],
    }]

    feature_value = efel.getFeatureValues(traces, ['voltage_base'])
    if feature_value is None:
        raise PSPError('Something went wrong when computing efel voltage_base')

    return feature_value[0]['voltage_base'][0]


def compute_scaling(psp1, psp2, v_holding, syn_type, params):
    """ Compute conductance scaling factor. """
    if syn_type not in {'EXC', 'INH'}:
        raise PSPError('syn_type must be one of EXC or INH, not: {}'.format(syn_type))

    E_rev = {
        'EXC': params.get('e_AMPA', 0.0),
        'INH': params.get('e_GABAA', -80.0),
    }[syn_type]

    d = np.abs(E_rev - v_holding)
    return (psp2 * (1 - (psp1 / d))) / (psp1 * (1 - (psp2 / d)))


def get_synapse_type(circuit, cell_group):
    """
    Get synapse type for `cell_group` cells.

    Raise an Exception if there are cells of more than one synapse type.
    """
    syn_types = circuit.cells.get(cell_group, Cell.SYNAPSE_CLASS).unique()
    if len(syn_types) != 1:
        raise PSPError(
            "Cell group should consist of cells with same synapse type, found: [{}]".format(
                ",".join(syn_types)
            )
        )
    return syn_types[0]
