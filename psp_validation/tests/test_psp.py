import os
from nose import tools as ntools
import numpy as np

import math
from itertools import repeat
from psp_validation import psp


_bconfig = "psp_validation/tests/input_data/sim_tencell_example1/RefBlueConfig_Scaling"

_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_data")


def test_get_peak_voltage_INH() :
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 9, 10)
    peak = np.min(voltage)
    ntools.assert_equal(peak, psp.get_peak_voltage(time, voltage, 0., "INH"))


def test_get_peak_voltage_EXC_with_timecut() :
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 9, 10)
    t_stim = 3
    peak = np.max(voltage[time > t_stim])
    ntools.assert_equal(peak, psp.get_peak_voltage(time, voltage, t_stim, "EXC"))


def test_get_peak_voltage_INH_with_timecut() :
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 0, 10)
    t_stim = 3
    peak = np.min(voltage[time > t_stim])
    ntools.assert_equal(peak, psp.get_peak_voltage(time, voltage, t_stim, "INH"))


@ntools.raises(Exception)
def test_get_peak_voltage_EXC_with_empty_input_raises() :
    psp.get_peak_voltage([], [], 0, "EXC")


@ntools.raises(Exception)
def test_get_peak_voltage_INH_with_empty_input_raises() :
    psp.get_peak_voltage([], [], 0, "INH")


@ntools.raises(Exception)
def test_get_peak_voltage_EXC_with_future_t_stim_raises() :
    psp.get_peak_voltage(np.array[0, 1, 2, 3], [11, 22, 33, 11], 4, "EXC")


@ntools.raises(Exception)
def test_get_peak_voltage_INH_with_future_t_stim_raises() :
    psp.get_peak_voltage(np.array[0, 1, 2, 3], [11, 22, 33, 11], 4, "INH")


@ntools.raises(ValueError)
def test_getpeak_voltage_call_with_non_numpy_array_args_raises() :
    psp.get_peak_voltage([0, 1, 2, 3], [11, 22, 33, 11], 0, "XXX")


def test_numpy_ndarray_checker() :
    psp._check_numpy_ndarrays(np.array([1,2,3]))
    psp._check_numpy_ndarrays(np.array([1,2,3]), np.array([1,2,3]))
    psp._check_numpy_ndarrays(np.array([1,2,3]), np.array([1,2,3]), np.array([1,2,3]))


@ntools.raises(ValueError)
def test_numpy_ndarray_checker_raises0() :
    psp._check_numpy_ndarrays([1,2,3], np.array([1,2,3]))


@ntools.raises(ValueError)
def test_numpy_ndarray_checker_raises1() :
    psp._check_numpy_ndarrays(np.array([1,2,3]), [1,2,3])


@ntools.raises(ValueError)
def test_numpy_ndarray_checker_raises2() :
    psp._check_numpy_ndarrays(np.array([1,2,3]), (1,2,3))


@ntools.raises(ValueError)
def test_numpy_ndarray_checker_raises3() :
   psp._check_numpy_ndarrays(1, 2, 3, "Hello")


def test_get_peak_amplitude() :
    # Use numpy to read the trace data from the txt file
    data = np.loadtxt(os.path.join(os.path.dirname(__file__), 'input_data', 'example_trace.txt'))

    ntools.assert_almost_equal(45.36493144290979,
                               psp.get_peak_amplitude(time=data[:, 0],
                                                      voltage=data[:, 1],
                                                      t_stim=1400,
                                                      syn_type='EXC'))

    ntools.assert_almost_equal(40.91181329374111,
                               psp.get_peak_amplitude(time=data[:, 0],
                                                      voltage=data[:, 1],
                                                      t_stim=1400,
                                                      syn_type='INH'))



def _make_traces(vss, ts):
    return list(zip(vss, repeat(ts)))


def test_SpikeFilter_members() :
    sf = psp.SpikeFilter(4321, 1234)
    ntools.assert_equal(sf.t0, 4321)
    ntools.assert_equal(sf.v_max, 1234)


def test_SpikeFilter_no_filter() :
    t = np.linspace(1, 10, 100)
    v = np.linspace(-10, 9, 100)
    traces = _make_traces(repeat(v, 5), t)
    sf = psp.SpikeFilter(0, 10)
    filtered = sf(traces)
    vs = [x[0] for x in traces]
    ntools.assert_equal(len(filtered[0]), len(vs))
    ntools.assert_equal(filtered[0], vs)


def test_SpikeFilter_filter_all() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i)
    traces = _make_traces(v, t)
    sf = psp.SpikeFilter(0, -5)
    filtered = sf(traces)
    vs = [x[0] for x in traces]
    ntools.assert_equal(len(filtered[0]), 0)
    ntools.assert_equal(filtered[0], [])


def test_SpikeFilter_filter() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i)
    traces = _make_traces(v, t)
    sf = psp.SpikeFilter(0, 25)
    filtered = sf(traces)
    vs = [x[0] for x in traces]
    ntools.assert_equal(len(filtered[0]), 3)
    ntools.assert_equal(filtered[0], vs[:3])



def test_defaultSpikeFilter() :
    f = psp.default_spike_filter(42)
    ntools.assert_equal(f.t0, 42)
    ntools.assert_equal(f.v_max, -20)


def test_mean_pair_voltage_from_traces_no_filter() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i) # 0, 10, 20, 30, 40 : mean is 20
    traces = _make_traces(v, t)
    mean = psp.mean_pair_voltage_from_traces(traces)
    ntools.assert_true(np.all(mean[0] == 20.))
    ntools.assert_true(np.all(mean[1] == t))
    ntools.assert_true(np.all(mean[2] == v))


def test_mean_pair_voltage_from_traces_filter() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i) # 0, 10, 20, 30, 40 : mean is 20
    traces = _make_traces(v, t)
    sf = psp.SpikeFilter(0, 25)
    mean = psp.mean_pair_voltage_from_traces(traces, sf)
    ntools.assert_true(np.all(mean[0] == 10.))
    ntools.assert_true(np.all(mean[1] == t))
    ntools.assert_true(np.all(mean[2] == v[:3]))


def test_mean_pair_voltage_from_traces_filter_all_returns_nan() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i) # 0, 10, 20, 30, 40 : mean is 20
    traces = _make_traces(v, t)
    sf = psp.SpikeFilter(0, -5)
    mean = psp.mean_pair_voltage_from_traces(traces, sf)
    ntools.assert_equal(mean, (None, None, [], None))


def test_amplitude_from_traces() :
    t = np.linspace(1, 900., 100)
    v = [np.empty(100) for i in range(5)]
    # create a "trace" with baseline -80mV and peak -46mV
    # Amplitude is |-80mV - -46mV| = 34mV
    for i, x in enumerate(v) :
        x.fill(-80.)
        x[90] = -50.
        x[91] = -48.
        x[92] = -46.
        x[93] = -48.
        x[94] = -50.
    t_stim = 800.
    t_start = t_stim - 10
    trace_filter = psp.SpikeFilter(t_start, v_max = 0)

    traces = _make_traces(v, t)
    amplitude = psp.calculate_amplitude(traces, 'EXC', trace_filter, t_stim)
    ntools.assert_equal(amplitude, 33.99243604007126)


def test_amplitude_from_traces_filter_all_returns_nan() :
    t = np.linspace(1, 900., 100)
    v = [np.empty(100) for i in range(5)]
    # create a "trace" with baseline -80mV and peak -46mV
    # Amplitude is |-80mV - -46mV| = 34mV
    for i, x in enumerate(v) :
        x.fill(-80.)
        x[90] = -50.
        x[91] = -48.
        x[92] = -46.
        x[93] = -48.
        x[94] = -50.
    t_stim = 800.
    t_start = t_stim - 10
    trace_filter = psp.SpikeFilter(t_start, v_max = -100)

    traces = _make_traces(v, t)
    amplitude = psp.calculate_amplitude(traces, 'EXC', trace_filter, t_stim)
    ntools.assert_true(np.isnan(amplitude))


def test_compute_scaling_EXC():
    result = psp.compute_scaling(1.0, 2.0, -70.0, 'EXC')
    ntools.assert_almost_equal(result, 2.029411764)


def test_compute_scaling_INH():
    result = psp.compute_scaling(1.0, 2.0, -70.0, 'INH')
    ntools.assert_almost_equal(result, 2.25)


def test_compute_scaling_invalid():
    ntools.assert_raises(AttributeError, psp.compute_scaling, 1.0, 2.0, -70, 'err')
