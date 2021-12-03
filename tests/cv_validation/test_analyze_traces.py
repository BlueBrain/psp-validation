import numpy as np
from unittest.mock import patch
from numpy.testing import assert_array_equal, assert_array_almost_equal
import psp_validation.cv_validation.analyze_traces as test_module


def test__filter_traces():
    t = np.arange(0, 100, .1)
    t_stim = 60
    traces = np.full((2, len(t)), -50)
    traces[1, -10] = 0  # add late spike

    # check that the trace with a late spike is filtered out
    res = test_module._filter_traces(t, traces, t_stim)
    assert_array_equal(res, [traces[0, :]])

    # check that None is return if all traces filtered out
    traces[0, -10] = 0
    res = test_module._filter_traces(t, traces, t_stim)
    assert res is None


def test__get_peak_amplitudes():
    t = np.arange(0, 100, .1)
    t_stim = 60
    base = -50.0
    traces = np.full((1, len(t)), base)

    peak = -40.0
    traces[:, -10] = peak
    res = test_module._get_peak_amplitudes(t, traces, 'EXC', t_stim)
    assert_array_almost_equal(res, [peak - base])

    peak = -60.0
    traces[:, -10] = peak
    res = test_module._get_peak_amplitudes(t, traces, 'INH', t_stim)
    assert_array_almost_equal(res, [base - peak])


def test__get_jackknife_traces():
    traces = np.hstack((np.eye(11), np.zeros((11, 1))))
    expected = np.hstack((np.full((11, 11), 0.1) - np.eye(11) * 0.1, np.full((11, 1), 0)))

    res = test_module._get_jackknife_traces(traces)
    assert_array_equal(res, expected)


@patch('psp_validation.cv_validation.analyze_traces._get_jackknife_traces')
def test_calc_cv(*_):
    t = np.arange(0, 1, 0.1)
    np.random.seed(1)
    amplitudes = np.random.random(10)
    with patch('psp_validation.cv_validation.analyze_traces._get_peak_amplitudes') as patched:
        patched.return_value = amplitudes
        expected = np.std(amplitudes) / np.mean(amplitudes)
        assert test_module.calc_cv(None, None, None, None, False) == expected

        # Since JK_var = (n-1)/n * SUM_SQUARES, and Var = 1/n * SUM_SQUARES
        expected = np.sqrt(len(amplitudes) - 1) * np.std(amplitudes) / np.mean(amplitudes)
        assert test_module.calc_cv(None, None, None, None, True) == expected
