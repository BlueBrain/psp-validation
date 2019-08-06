import os
from os.path import dirname
from mock import patch

from nose.tools import ok_, assert_equal, assert_raises, raises, assert_almost_equal, assert_true
import numpy as np

import math
from itertools import repeat
from psp_validation import psp
from psp_validation.tests.utils import mock_run_pair_simulation_suite, setup_tempdir


_bconfig = "psp_validation/tests/input_data/sim_tencell_example1/RefBlueConfig_Scaling"

_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_data")


def test_get_peak_voltage_INH() :
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 9, 10)
    peak = np.min(voltage)
    assert_equal(peak, psp.get_peak_voltage(time, voltage, 0., "INH"))


def test_get_peak_voltage_EXC_with_timecut() :
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 9, 10)
    t_stim = 3
    peak = np.max(voltage[time > t_stim])
    assert_equal(peak, psp.get_peak_voltage(time, voltage, t_stim, "EXC"))


def test_get_peak_voltage_INH_with_timecut() :
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 0, 10)
    t_stim = 3
    peak = np.min(voltage[time > t_stim])
    assert_equal(peak, psp.get_peak_voltage(time, voltage, t_stim, "INH"))


@raises(Exception)
def test_get_peak_voltage_EXC_with_empty_input_raises() :
    psp.get_peak_voltage([], [], 0, "EXC")


@raises(Exception)
def test_get_peak_voltage_INH_with_empty_input_raises() :
    psp.get_peak_voltage([], [], 0, "INH")


@raises(Exception)
def test_get_peak_voltage_EXC_with_future_t_stim_raises() :
    psp.get_peak_voltage(np.array[0, 1, 2, 3], [11, 22, 33, 11], 4, "EXC")


@raises(Exception)
def test_get_peak_voltage_INH_with_future_t_stim_raises() :
    psp.get_peak_voltage(np.array[0, 1, 2, 3], [11, 22, 33, 11], 4, "INH")


@raises(ValueError)
def test_getpeak_voltage_call_with_non_numpy_array_args_raises() :
    psp.get_peak_voltage([0, 1, 2, 3], [11, 22, 33, 11], 0, "XXX")


def test_numpy_ndarray_checker() :
    psp._check_numpy_ndarrays(np.array([1,2,3]))
    psp._check_numpy_ndarrays(np.array([1,2,3]), np.array([1,2,3]))
    psp._check_numpy_ndarrays(np.array([1,2,3]), np.array([1,2,3]), np.array([1,2,3]))


@raises(ValueError)
def test_numpy_ndarray_checker_raises0() :
    psp._check_numpy_ndarrays([1,2,3], np.array([1,2,3]))


@raises(ValueError)
def test_numpy_ndarray_checker_raises1() :
    psp._check_numpy_ndarrays(np.array([1,2,3]), [1,2,3])


@raises(ValueError)
def test_numpy_ndarray_checker_raises2() :
    psp._check_numpy_ndarrays(np.array([1,2,3]), (1,2,3))


@raises(ValueError)
def test_numpy_ndarray_checker_raises3() :
   psp._check_numpy_ndarrays(1, 2, 3, "Hello")


def test_get_peak_amplitude() :
    # Use numpy to read the trace data from the txt file
    data = np.loadtxt(os.path.join(os.path.dirname(__file__), 'input_data', 'example_trace.txt'))

    assert_almost_equal(45.36493144290979,
                               psp.get_peak_amplitude(time=data[:, 0],
                                                      voltage=data[:, 1],
                                                      t_stim=1400,
                                                      syn_type='EXC'))

    assert_almost_equal(40.91181329374111,
                               psp.get_peak_amplitude(time=data[:, 0],
                                                      voltage=data[:, 1],
                                                      t_stim=1400,
                                                      syn_type='INH'))



def _make_traces(vss, ts):
    return list(zip(vss, repeat(ts)))


def test_SpikeFilter_members() :
    sf = psp.SpikeFilter(4321, 1234)
    assert_equal(sf.t0, 4321)
    assert_equal(sf.v_max, 1234)


def test_SpikeFilter_no_filter() :
    t = np.linspace(1, 10, 100)
    v = np.linspace(-10, 9, 100)
    traces = _make_traces(repeat(v, 5), t)
    sf = psp.SpikeFilter(0, 10)
    filtered = sf(traces)
    vs = [x[0] for x in traces]
    assert_equal(len(filtered[0]), len(vs))
    assert_equal(filtered[0], vs)


def test_SpikeFilter_filter_all() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i)
    traces = _make_traces(v, t)
    sf = psp.SpikeFilter(0, -5)
    filtered = sf(traces)
    vs = [x[0] for x in traces]
    assert_equal(len(filtered[0]), 0)
    assert_equal(filtered[0], [])


def test_SpikeFilter_filter() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i)
    traces = _make_traces(v, t)
    sf = psp.SpikeFilter(0, 25)
    filtered = sf(traces)
    vs = [x[0] for x in traces]
    assert_equal(len(filtered[0]), 3)
    assert_equal(filtered[0], vs[:3])



def test_defaultSpikeFilter() :
    f = psp.default_spike_filter(42)
    assert_equal(f.t0, 42)
    assert_equal(f.v_max, -20)


def test_mean_pair_voltage_from_traces_no_filter() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i) # 0, 10, 20, 30, 40 : mean is 20
    traces = _make_traces(v, t)
    mean = psp.mean_pair_voltage_from_traces(traces)
    assert_true(np.all(mean[0] == 20.))
    assert_true(np.all(mean[1] == t))
    assert_true(np.all(mean[2] == v))


def test_mean_pair_voltage_from_traces_filter() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i) # 0, 10, 20, 30, 40 : mean is 20
    traces = _make_traces(v, t)
    sf = psp.SpikeFilter(0, 25)
    mean = psp.mean_pair_voltage_from_traces(traces, sf)
    assert_true(np.all(mean[0] == 10.))
    assert_true(np.all(mean[1] == t))
    assert_true(np.all(mean[2] == v[:3]))


def test_mean_pair_voltage_from_traces_filter_all_returns_nan() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i) # 0, 10, 20, 30, 40 : mean is 20
    traces = _make_traces(v, t)
    sf = psp.SpikeFilter(0, -5)
    mean = psp.mean_pair_voltage_from_traces(traces, sf)
    assert_equal(mean, (None, None, [], None))


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
    assert_equal(amplitude, 33.99243604007126)


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
    assert_true(np.isnan(amplitude))


def test_compute_scaling_EXC():
    result = psp.compute_scaling(1.0, 2.0, -70.0, 'EXC', {})
    assert_almost_equal(result, 2.029411764)


def test_compute_scaling_INH():
    result = psp.compute_scaling(1.0, 2.0, -70.0, 'INH', {})
    assert_almost_equal(result, 2.25)

    result = psp.compute_scaling(1.0, 2.0, -70.0, 'INH', {'e_GABAA': -94.0})
    assert_almost_equal(result, 2.0909090909)


def test_compute_scaling_invalid():
    assert_raises(AttributeError, psp.compute_scaling, 1.0, 2.0, -70, 'err', {})



@patch('psp_validation.psp._import_run_pair_simulation_suite', return_value=mock_run_pair_simulation_suite)
@patch('psp_validation.psp.get_pairs', side_effect=lambda *args, **kargs: [(14194, 14494)])
@patch('psp_validation.psp.bluepy.Circuit')
@patch('psp_validation.psp.get_synapse_type', return_value='EXC')
def test_run(m1, m2, m3, m4):
    hippo_path = os.path.join(dirname(__file__), '..', '..', 'usecases', 'hippocampus')

    with setup_tempdir('test-psp-run') as folder:
        psp.run(
            [os.path.join(hippo_path, 'pathways', 'SP_PC-SP_PC.yaml')],
            os.path.join(dirname(__file__), 'input_data', 'Ref_BlueConfig'),
            os.path.join(hippo_path, 'targets.yaml'),
            folder,
            num_pairs=1,
            num_trials=1,
            clamp='current',
            dump_traces=True,
            dump_amplitudes=True,
            seed=None,
            jobs=1,
        )
        ok_(os.path.exists(os.path.join(folder, 'SP_PC-SP_PC.summary.yaml')))
