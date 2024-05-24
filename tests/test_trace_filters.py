from itertools import repeat

import numpy as np
from numpy.testing import assert_array_equal

import psp_validation.trace_filters as test_module

from tests.utils import _make_traces


def test_NullFilter_no_filter():
    t = np.linspace(1, 10, 100)
    vs = [np.full(100, 10.0 * i) for i in range(5)]
    traces = _make_traces(vs, t)

    tf = test_module.NullFilter()
    filtered = np.array(tf(traces))

    assert filtered.shape == (5, 2, 100)
    assert_array_equal(filtered, traces)


def test_NullFilter_filter_all():
    traces = [
        ([], []),
        (np.array([]), np.array([])),
        (None, None),
    ]

    tf = test_module.NullFilter()
    filtered = np.array(tf(traces))

    assert filtered.shape == (0,)
    assert_array_equal(filtered, [])


def test_SpikeFilter_members():
    tf = test_module.SpikeFilter(4321, 1234)

    assert tf.t0 == 4321
    assert tf.v_max == 1234


def test_SpikeFilter_no_filter():
    t = np.linspace(1, 10, 100)
    v = np.linspace(-10, 9, 100)
    traces = _make_traces(repeat(v, 5), t)

    tf = test_module.SpikeFilter(0, 10)
    filtered = np.array(tf(traces))

    assert filtered.shape == (5, 2, 100)
    assert_array_equal(filtered, traces)


def test_SpikeFilter_filter_all():
    t = np.linspace(1, 10, 100)
    v = [np.full(100, 10.0 * i) for i in range(5)]
    traces = _make_traces(v, t)

    tf = test_module.SpikeFilter(0, -5)
    filtered = np.array(tf(traces))

    assert filtered.shape == (0,)
    assert_array_equal(filtered, [])


def test_SpikeFilter_filter():
    t = np.linspace(1, 10, 100)
    v = [np.full(100, 10.0 * i) for i in range(5)]
    traces = _make_traces(v, t)

    tf = test_module.SpikeFilter(0, 25)
    filtered = np.array(tf(traces))

    assert filtered.shape == (3, 2, 100)
    assert_array_equal(filtered, traces[:3])


def test_AmplitudeFilter_members():
    tf = test_module.AmplitudeFilter(2345, 0.12, "EXC")

    assert tf.t_stim == 2345
    assert tf.min_trace_amplitude == 0.12
    assert tf.syn_type == "EXC"


def test_AmplitudeFilter_no_filter_with_zero_amplitude():
    t = np.linspace(1, 10, 100)
    v = np.full(100, -70)
    traces = _make_traces(repeat(v, 5), t)

    tf = test_module.AmplitudeFilter(2, 0, "EXC")
    filtered = np.array(tf(traces))

    assert filtered.shape == (5, 2, 100)
    assert_array_equal(filtered, traces)


def test_AmplitudeFilter_no_filter_exc():
    t = np.linspace(1, 10, 100)
    v = np.full(100, -70)
    v[30:40] += 10  # perturbation
    traces = _make_traces(repeat(v, 5), t)

    tf = test_module.AmplitudeFilter(2, 9, "EXC")
    filtered = np.array(tf(traces))

    assert filtered.shape == (5, 2, 100)
    assert_array_equal(filtered, traces)


def test_AmplitudeFilter_no_filter_inh():
    t = np.linspace(1, 10, 100)
    v = np.full(100, -70)
    v[30:40] -= 10  # perturbation
    traces = _make_traces(repeat(v, 5), t)

    tf = test_module.AmplitudeFilter(2, 9, "INH")
    filtered = np.array(tf(traces))

    assert filtered.shape == (5, 2, 100)
    assert_array_equal(filtered, traces)


def test_AmplitudeFilter_filter_all_exc():
    t = np.linspace(1, 10, 100)
    v = np.full(100, -70)
    v[30:40] -= 10  # perturbation
    traces = _make_traces(repeat(v, 5), t)

    tf = test_module.AmplitudeFilter(2, 9, "EXC")
    filtered = np.array(tf(traces))

    assert filtered.shape == (0,)
    assert_array_equal(filtered, [])


def test_AmplitudeFilter_filter_all_inh():
    t = np.linspace(1, 10, 100)
    v = np.full(100, -70)
    v[30:40] += 10  # perturbation
    traces = _make_traces(repeat(v, 5), t)

    tf = test_module.AmplitudeFilter(2, 9, "INH")
    filtered = np.array(tf(traces))

    assert filtered.shape == (0,)
    assert_array_equal(filtered, [])


def test_AmplitudeFilter_filter_all_flat_exc():
    t = np.linspace(1, 10, 100)
    v = np.full(100, -70)
    traces = _make_traces(repeat(v, 5), t)

    tf = test_module.AmplitudeFilter(2, 9, "EXC")
    filtered = np.array(tf(traces))

    assert filtered.shape == (0,)
    assert_array_equal(filtered, [])


def test_AmplitudeFilter_filter_all_flat_inh():
    t = np.linspace(1, 10, 100)
    v = np.full(100, -70)
    traces = _make_traces(repeat(v, 5), t)

    tf = test_module.AmplitudeFilter(2, 9, "INH")
    filtered = np.array(tf(traces))

    assert filtered.shape == (0,)
    assert_array_equal(filtered, [])


def test_AmplitudeFilter_filter():
    t = np.linspace(1, 10, 100)
    vs = [np.full(100, 10.0 * i) for i in range(6)]
    vs[0][30:40] += 10  # perturbation
    vs[1][50:60] += 5  # perturbation
    vs[2][70:80] += 15  # perturbation
    vs[3][30:40] += 1  # too small perturbation (trace should be filtered out)
    vs[4][30:40] -= 10  # negative perturbation (ignored in EXC)
    traces = _make_traces(vs, t)

    tf = test_module.AmplitudeFilter(2, 4, "EXC")
    filtered = np.array(tf(traces))

    assert filtered.shape == (3, 2, 100)
    assert_array_equal(filtered, traces[:3])
