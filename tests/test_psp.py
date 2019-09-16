import h5py
import os
from os.path import dirname
from mock import patch, MagicMock

from nose.tools import ok_, assert_equal, assert_raises, raises, assert_almost_equal, assert_true, assert_dict_equal
import numpy as np
from numpy.testing import assert_array_equal

import math
from itertools import repeat
from psp_validation import psp
from .utils import mock_run_pair_simulation_suite, setup_tempdir


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
    mean = psp.mean_pair_voltage_from_traces(traces, psp.SpikeFilter(0, 100))
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


def test__init_traces_dump():
    with setup_tempdir('test-init-traces-dump') as folder:
        traces_path = psp._init_traces_dump(folder, 'title', 'current')

        with h5py.File(traces_path, 'r') as h5f:
            assert_equal(h5f.attrs['data'], 'voltage')

    with setup_tempdir('test-init-traces-dump') as folder:
        traces_path = psp._init_traces_dump(folder, 'title', 'voltage')

        with h5py.File(traces_path, 'r') as h5f:
            assert_equal(h5f.attrs['data'], 'current')


def test__run_one_pair():
    sim_runner = MagicMock(return_value=mock_run_pair_simulation_suite())
    protocol_params = psp.ProtocolParameters(
        clamp='current',
        circuit=MagicMock(),
        targets=MagicMock(),
        num_pairs=99,
        num_trials=12,
        dump_amplitudes=True,
        dump_traces=True)
    pathway_params = psp.PathwayParameters(
        pathway=dict(),
        projection=dict(),
        pairs=[(1, 2)],
        pre_syn_type='EXC',
        min_ampl=12.3,
        protocol=dict(),
        t_stim=199.,
        spike_filter=psp.SpikeFilter(t_start=0, v_max=100))
    all_amplitudes = list()


    with setup_tempdir('test-run-one-pair') as folder:
        h5_file = os.path.join(folder, 'dump.h5')
        psp._run_one_pair(sim_runner,
                          0,
                          protocol_params, pathway_params, all_amplitudes, h5_file)
        assert_almost_equal(all_amplitudes, [94.0238021084036])

        with h5py.File(h5_file, 'r') as f:
            ok_('/traces/a1-a2' in f)
            group = f['/traces/a1-a2']
            assert_equal(group.attrs['pre_gid'], 1)
            assert_equal(group.attrs['post_gid'], 2)
            ok_('trials' in group)
            ok_('average' in group)

@patch('psp_validation.psp.get_synapse_type', return_value='EXC')
def test__run_pathway_no_pairs(m1):
    protocol_params = psp.ProtocolParameters(
        clamp='current',
        circuit=MagicMock(),
        targets=MagicMock(),
        num_pairs=99,
        num_trials=12,
        dump_amplitudes=True,
        dump_traces=True)


    with setup_tempdir('test-run-pathway') as folder:
        psp._run_pathway(os.path.join(_path, 'pathway.yaml'),
                         folder, MagicMock(), protocol_params)
        assert_array_equal(os.listdir(folder),
                           ['pathway.traces.h5'])
        with h5py.File(os.path.join(folder, 'pathway.traces.h5'), 'r') as f:
            assert_array_equal(list(f.keys()), [])

@patch('psp_validation.psp.get_synapse_type', return_value='EXC')
@patch('psp_validation.psp._get_pathway_parameters', return_value=psp.PathwayParameters(
    pathway={'pre': 'SP_PC',
             'post': 'SP_PVBC',
             'constraints': {'max_dist_x': 100.0,
                             'max_dist_y': 100.0,
                             'max_dist_z': 100.0}},
    projection=None,
    pairs=[(1, 2)],
    pre_syn_type='EXC',
    min_ampl=0.0,
    protocol={'record_dt': 0.1,
              'hold_V': -70.0,
              't_stim': 800.0,
              't_stop': 900.0,
              'post_ttx': False},
    t_stim=800.0, spike_filter=psp.SpikeFilter(t_start=0, v_max=100)))
def test__run_pathway(mock_get_pathway_parameters, mock_get_synapse_type):
    protocol_params = psp.ProtocolParameters(
        clamp='current',
        circuit=MagicMock(),
        targets=MagicMock(),
        num_pairs=99,
        num_trials=12,
        dump_amplitudes=True,
        dump_traces=True)


    with setup_tempdir('test-run-pathway-dump-trace') as folder:
        protocol_params.dump_traces = True
        psp._run_pathway(os.path.join(_path, 'pathway.yaml'),
                         folder,
                         sim_runner=MagicMock(return_value=mock_run_pair_simulation_suite()),
                         protocol_params=protocol_params)
        assert_array_equal(list(sorted(os.listdir(folder))),
                           ['pathway.amplitudes.txt', 'pathway.summary.yaml', 'pathway.traces.h5'])
        with h5py.File(os.path.join(folder, 'pathway.traces.h5'), 'r') as f:
            assert_array_equal(list(f['traces']['a1-a2'].keys()), ['average', 'trials'])

    with setup_tempdir('test-run-pathway') as folder:
        protocol_params.dump_traces = False
        psp._run_pathway(os.path.join(_path, 'pathway.yaml'),
                         folder,
                         sim_runner=MagicMock(return_value=mock_run_pair_simulation_suite()),
                         protocol_params=protocol_params)
        assert_array_equal(list(sorted(os.listdir(folder))),
                           ['pathway.amplitudes.txt', 'pathway.summary.yaml'])



@patch('psp_validation.psp.run_pair_simulation_suite',
       return_value=mock_run_pair_simulation_suite())
@patch('psp_validation.psp.get_pairs', side_effect=lambda *args, **kargs: [(14194, 14494)])
@patch('psp_validation.psp.bluepy.Circuit')
@patch('psp_validation.psp.get_synapse_type', return_value='EXC')
def test_run(m1, m2, m3, m4):
    hippo_path = os.path.join(dirname(__file__), '..', 'usecases', 'hippocampus')

    with setup_tempdir('test-psp-run') as folder:
        psp.run(
            [os.path.join(_path, 'pathway.yaml')],
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
        ok_(os.path.exists(os.path.join(folder, 'pathway.summary.yaml')))
