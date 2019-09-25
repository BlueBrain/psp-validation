from mock import patch, MagicMock
from itertools import repeat
import pandas as pd
import os

import numpy as np
from numpy.testing import assert_array_equal
from nose.tools import (assert_almost_equal, assert_dict_equal, assert_equal,
                        assert_raises, assert_true, ok_, raises)

from psp_validation import PSPError
import psp_validation.features as test_module
from psp_validation.simulation import SimulationResult
from .utils import _make_traces, mock_run_pair_simulation_suite


_bconfig = "psp_validation/tests/input_data/sim_tencell_example1/RefBlueConfig_Scaling"

_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_data")

def test_get_peak_voltage_INH() :
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 9, 10)
    peak = np.min(voltage)
    assert_equal(peak, test_module.get_peak_voltage(time, voltage, 0., "INH"))


def test_get_peak_voltage_EXC_with_timecut() :
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 9, 10)
    t_stim = 3
    peak = np.max(voltage[time > t_stim])
    assert_equal(peak, test_module.get_peak_voltage(time, voltage, t_stim, "EXC"))


def test_get_peak_voltage_INH_with_timecut() :
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 0, 10)
    t_stim = 3
    peak = np.min(voltage[time > t_stim])
    assert_equal(peak, test_module.get_peak_voltage(time, voltage, t_stim, "INH"))


def test__check_syntype():
    test_module._check_syn_type("EXC")
    test_module._check_syn_type("INH")
    assert_raises(AttributeError, test_module._check_syn_type, "gloubi-boulga")



@raises(Exception)
def test_get_peak_voltage_EXC_with_empty_input_raises() :
    test_module.get_peak_voltage([], [], 0, "EXC")


@raises(Exception)
def test_get_peak_voltage_INH_with_empty_input_raises() :
    test_module.get_peak_voltage([], [], 0, "INH")


@raises(Exception)
def test_get_peak_voltage_EXC_with_future_t_stim_raises() :
    test_module.get_peak_voltage(np.array[0, 1, 2, 3], [11, 22, 33, 11], 4, "EXC")


@raises(Exception)
def test_get_peak_voltage_INH_with_future_t_stim_raises() :
    test_module.get_peak_voltage(np.array[0, 1, 2, 3], [11, 22, 33, 11], 4, "INH")


@raises(ValueError)
def test_getpeak_voltage_call_with_non_numpy_array_args_raises() :
    test_module.get_peak_voltage([0, 1, 2, 3], [11, 22, 33, 11], 0, "XXX")


def test_numpy_ndarray_checker() :
    test_module._check_numpy_ndarrays(np.array([1,2,3]))
    test_module._check_numpy_ndarrays(np.array([1,2,3]), np.array([1,2,3]))
    test_module._check_numpy_ndarrays(np.array([1,2,3]), np.array([1,2,3]), np.array([1,2,3]))


@raises(ValueError)
def test_numpy_ndarray_checker_raises0() :
    test_module._check_numpy_ndarrays([1,2,3], np.array([1,2,3]))


@raises(ValueError)
def test_numpy_ndarray_checker_raises1() :
    test_module._check_numpy_ndarrays(np.array([1,2,3]), [1,2,3])


@raises(ValueError)
def test_numpy_ndarray_checker_raises2() :
    test_module._check_numpy_ndarrays(np.array([1,2,3]), (1,2,3))


@raises(ValueError)
def test_numpy_ndarray_checker_raises3() :
   test_module._check_numpy_ndarrays(1, 2, 3, "Hello")


def test_get_peak_amplitude() :
    # Use numpy to read the trace data from the txt file
    data = np.loadtxt(os.path.join(os.path.dirname(__file__), 'input_data', 'example_trace.txt'))

    assert_almost_equal(45.36493144290979,
                               test_module.get_peak_amplitude(time=data[:, 0],
                                                      voltage=data[:, 1],
                                                      t_stim=1400,
                                                      syn_type='EXC'))

    assert_almost_equal(40.91181329374111,
                               test_module.get_peak_amplitude(time=data[:, 0],
                                                      voltage=data[:, 1],
                                                      t_stim=1400,
                                                      syn_type='INH'))

def test_SpikeFilter_members() :
    sf = test_module.SpikeFilter(4321, 1234)
    assert_equal(sf.t0, 4321)
    assert_equal(sf.v_max, 1234)


def test_SpikeFilter_no_filter() :
    t = np.linspace(1, 10, 100)
    v = np.linspace(-10, 9, 100)
    traces = _make_traces(repeat(v, 5), t)
    sf = test_module.SpikeFilter(0, 10)
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
    sf = test_module.SpikeFilter(0, -5)
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
    sf = test_module.SpikeFilter(0, 25)
    filtered = sf(traces)
    vs = [x[0] for x in traces]
    assert_equal(len(filtered[0]), 3)
    assert_equal(filtered[0], vs[:3])


def test_defaultSpikeFilter() :
    f = test_module.default_spike_filter(42)
    assert_equal(f.t0, 42)
    assert_equal(f.v_max, -20)


def test_mean_pair_voltage_from_traces_no_filter() :
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i) # 0, 10, 20, 30, 40 : mean is 20
    results = SimulationResult({}, np.linspace(1, 10, 100), None, v)
    mean = test_module.mean_pair_voltage_from_traces(results, test_module.SpikeFilter(0, 100))
    assert_true(np.all(mean[0] == 20.))
    assert_true(np.all(mean[1] == results.time))
    assert_array_equal(mean[2], v)


def test_mean_pair_voltage_from_traces_filter() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i) # 0, 10, 20, 30, 40 : mean is 20
    results = SimulationResult({}, np.linspace(1, 10, 100), None, v)
    sf = test_module.SpikeFilter(0, 25)
    mean = test_module.mean_pair_voltage_from_traces(results, sf)
    assert_true(np.all(mean[0] == 10.))
    assert_true(np.all(mean[1] == t))
    assert_array_equal(mean[2], v[:3])


def test_mean_pair_voltage_from_traces_filter_all_returns_nan() :
    t = np.linspace(1, 10, 100)
    v = [np.empty(100) for i in range(5)]
    for i, x in enumerate(v) :
        x.fill(10*i) # 0, 10, 20, 30, 40 : mean is 20
    results = SimulationResult({}, np.linspace(1, 10, 100), None, v)
    sf = test_module.SpikeFilter(0, -5)
    mean = test_module.mean_pair_voltage_from_traces(results, sf)
    assert_equal(mean, (None, None, [], None))


def test_compute_scaling_EXC():
    result = test_module.compute_scaling(1.0, 2.0, -70.0, 'EXC', {})
    assert_almost_equal(result, 2.029411764)


def test_compute_scaling_INH():
    result = test_module.compute_scaling(1.0, 2.0, -70.0, 'INH', {})
    assert_almost_equal(result, 2.25)

    result = test_module.compute_scaling(1.0, 2.0, -70.0, 'INH', {'e_GABAA': -94.0})
    assert_almost_equal(result, 2.0909090909)

    result = test_module.compute_scaling(1.0, 2.0, -70.0, 'EXC', {})
    assert_almost_equal(result, 2.0294117647058827)

    result = test_module.compute_scaling(1.0, 2.0, -70.0, 'EXC', {'e_AMPA': -70.3})
    assert_almost_equal(result, 0.8235294117647078)


def test_compute_scaling_invalid():
    assert_raises(PSPError, test_module.compute_scaling, 1.0, 2.0, -70, 'err', {})


def test_resting_potential():
    result = mock_run_pair_simulation_suite()
    potential = test_module.resting_potential(result.time, result.voltages[0],  1000, 1400)
    assert_almost_equal(potential, -42.18599807850207)


    with patch('psp_validation.features.efel.getFeatureValues') as instance:
        instance.return_value = None
        assert_raises(PSPError, test_module.resting_potential,
                      result.time, result.voltages[0],  1000, 1400)

def test_get_synapse_type():
    circuit = MagicMock()
    circuit.cells.get.return_value = pd.Series(['EXC', 'EXC', 'EXC'])
    group = MagicMock()
    test_module.get_synapse_type(circuit, group)

    circuit.cells.get.return_value = pd.Series(['EXC', 'EXC', 'INH'])
    assert_raises(PSPError, test_module.get_synapse_type, circuit, group)
