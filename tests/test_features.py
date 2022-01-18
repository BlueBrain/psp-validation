import os

import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch

import pytest
from numpy.testing import assert_array_equal, assert_allclose

import psp_validation.features as test_module
from psp_validation import PSPError
from psp_validation.simulation import SimulationResult
from psp_validation.trace_filters import NullFilter, SpikeFilter

from .utils import mock_run_pair_simulation_suite

_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_data")


def test_get_peak_voltage_INH():
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 9, 10)
    peak = np.min(voltage)
    actual = test_module.get_peak_voltage(time, voltage, 0., "INH")
    assert peak == actual


def test_get_peak_voltage_EXC_with_timecut():
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 9, 10)
    t_stim = 3
    peak = np.max(voltage[time > t_stim])
    actual = test_module.get_peak_voltage(time, voltage, t_stim, "EXC")
    assert peak == actual


def test_get_peak_voltage_INH_with_timecut():
    time = np.linspace(1, 10, 10)
    voltage = np.linspace(-10, 0, 10)
    t_stim = 3
    peak = np.min(voltage[time > t_stim])
    actual = test_module.get_peak_voltage(time, voltage, t_stim, "INH")
    assert peak == actual


def test__check_syntype():
    test_module.check_syn_type("EXC")
    test_module.check_syn_type("INH")
    with pytest.raises(AttributeError):
        test_module.check_syn_type("gloubi-boulga")


def test_get_peak_voltage_EXC_with_empty_input_raises():
    with pytest.raises(ValueError):
        test_module.get_peak_voltage(np.array([]), np.array([]), 0, "EXC")


def test_get_peak_voltage_INH_with_empty_input_raises():
    with pytest.raises(ValueError):
        test_module.get_peak_voltage(np.array([]), np.array([]), 0, "INH")


def test_get_peak_voltage_EXC_with_future_t_stim_raises():
    with pytest.raises(ValueError):
        test_module.get_peak_voltage(np.array([0, 1, 2, 3]), np.array([11, 22, 33, 11]), 4, "EXC")


def test_get_peak_voltage_INH_with_future_t_stim_raises():
    with pytest.raises(ValueError):
        test_module.get_peak_voltage(np.array([0, 1, 2, 3]), np.array([11, 22, 33, 11]), 4, "INH")


def test_getpeak_voltage_call_with_non_numpy_array_args_raises():
    with pytest.raises(ValueError):
        test_module.get_peak_voltage([0, 1, 2, 3], [11, 22, 33, 11], 0, "XXX")


def test_numpy_ndarray_checker():
    test_module._check_numpy_ndarrays(np.array([1, 2, 3]))
    test_module._check_numpy_ndarrays(np.array([1, 2, 3]), np.array([1, 2, 3]))
    test_module._check_numpy_ndarrays(np.array([1, 2, 3]), np.array([1, 2, 3]), np.array([1, 2, 3]))


def test_numpy_ndarray_checker_raises0():
    with pytest.raises(ValueError):
        test_module._check_numpy_ndarrays([1, 2, 3], np.array([1, 2, 3]))


def test_numpy_ndarray_checker_raises1():
    with pytest.raises(ValueError):
        test_module._check_numpy_ndarrays(np.array([1, 2, 3]), [1, 2, 3])


def test_numpy_ndarray_checker_raises2():
    with pytest.raises(ValueError):
        test_module._check_numpy_ndarrays(np.array([1, 2, 3]), (1, 2, 3))


def test_numpy_ndarray_checker_raises3():
    with pytest.raises(ValueError):
        test_module._check_numpy_ndarrays(1, 2, 3, "Hello")


def test_get_peak_amplitude():
    # Use numpy to read the trace data from the txt file
    data = np.loadtxt(os.path.join(os.path.dirname(__file__), 'input_data', 'example_trace.txt'))

    actual = test_module.get_peak_amplitude(
        time=data[:, 0],
        voltage=data[:, 1],
        t_stim=1400,
        syn_type='EXC',
    )
    assert_allclose(45.36493144290979, actual)

    actual = test_module.get_peak_amplitude(
        time=data[:, 0],
        voltage=data[:, 1],
        t_stim=1400,
        syn_type='INH',
    )
    assert_allclose(40.91181329374111, actual)


def test_mean_pair_voltage_from_traces_no_filter():
    t = np.linspace(1, 10, 100)
    v = [np.full(100, 10.0 * i) for i in range(5)]  # 0, 10, 20, 30, 40 : mean is 20
    results = SimulationResult({}, t, None, v)
    traces = test_module.old_school_trace(results)
    filters = [NullFilter(), SpikeFilter(0, 100)]
    mean = test_module.mean_pair_voltage_from_traces(traces, filters)
    assert np.all(mean[0] == 20.)
    assert np.all(mean[1] == t)
    assert_array_equal(mean[2], v)


def test_mean_pair_voltage_from_traces_filter():
    t = np.linspace(1, 10, 100)
    v = [np.full(100, 10.0 * i) for i in range(5)]  # 0, 10, 20, 30, 40 : mean is 20
    results = SimulationResult({}, t, None, v)
    traces = test_module.old_school_trace(results)
    filters = [NullFilter(), SpikeFilter(0, 25)]
    mean = test_module.mean_pair_voltage_from_traces(traces, filters)
    assert np.all(mean[0] == 10.)
    assert np.all(mean[1] == t)
    assert_array_equal(mean[2], v[:3])


def test_mean_pair_voltage_from_traces_filter_all_returns_nan():
    t = np.linspace(1, 10, 100)
    v = [np.full(100, 10.0 * i) for i in range(5)]  # 0, 10, 20, 30, 40 : mean is 20
    results = SimulationResult({}, t, None, v)
    filters = [NullFilter(), SpikeFilter(0, -5)]
    traces = test_module.old_school_trace(results)
    mean = test_module.mean_pair_voltage_from_traces(traces, filters)
    assert mean == (None, None, [])


def test_compute_scaling_EXC():
    result = test_module.compute_scaling(1.0, 2.0, -70.0, 'EXC', {})
    assert_allclose(result, 2.029411764)


def test_compute_scaling_INH():
    result = test_module.compute_scaling(1.0, 2.0, -70.0, 'INH', {})
    assert_allclose(result, 2.25)

    result = test_module.compute_scaling(1.0, 2.0, -70.0, 'INH', {'e_GABAA': -94.0})
    assert_allclose(result, 2.0909090909)

    result = test_module.compute_scaling(1.0, 2.0, -70.0, 'EXC', {})
    assert_allclose(result, 2.0294117647058827)

    result = test_module.compute_scaling(1.0, 2.0, -70.0, 'EXC', {'e_AMPA': -70.3})
    assert_allclose(result, 0.8235294117647078)


def test_compute_scaling_invalid():
    with pytest.raises(PSPError):
        test_module.compute_scaling(1.0, 2.0, -70, 'err', {})


def test_resting_potential():
    result = mock_run_pair_simulation_suite()
    potential = test_module.resting_potential(result.time, result.voltages[0], 1000, 1400)
    assert_allclose(potential, -42.18599807850207)

    with patch('psp_validation.features.efel.getFeatureValues') as instance:
        instance.return_value = None
        with pytest.raises(PSPError):
            test_module.resting_potential(result.time, result.voltages[0], 1000, 1400)


def test_get_synapse_type():
    circuit = MagicMock()
    circuit.cells.get.return_value = pd.Series(['EXC', 'EXC', 'EXC'])
    group = MagicMock()
    test_module.get_synapse_type(circuit, group)

    circuit.cells.get.return_value = pd.Series(['EXC', 'EXC', 'INH'])
    with pytest.raises(PSPError):
        test_module.get_synapse_type(circuit, group)
