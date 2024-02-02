import os
from tempfile import TemporaryDirectory
import pandas as pd

import h5py
from unittest.mock import MagicMock, patch
from numpy.testing import assert_array_equal, assert_allclose

import psp_validation.pathways as test_module
from psp_validation.psp import ProtocolParameters
from psp_validation.trace_filters import SpikeFilter
from bluepysnap.circuit_ids import CircuitNodeId

from .utils import mock_run_pair_simulation_suite

_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_data")

_PATHWAY_PATH = os.path.join(_path, 'pathway.yaml')


def _default_protocol(**kwargs):
    circuit = MagicMock()
    circuit.nodes.get.return_value = [("population_name", pd.Series("dummy"))]
    args_ = dict(
        clamp='current',
        circuit=circuit,
        targets=MagicMock(),
        num_pairs=99,
        num_trials=12,
        dump_amplitudes=True,
        dump_traces=True,
        output_dir='a',
    )
    args_.update(kwargs)
    return ProtocolParameters(**args_)


@patch('psp_validation.pathways.get_synapse_type', return_value='EXC')
def _dummy_pathway(protocol_kwargs, synapse_type_mock):
    protocol = _default_protocol(**protocol_kwargs)
    sim_runner = MagicMock(return_value=mock_run_pair_simulation_suite())
    pathway = test_module.Pathway(_PATHWAY_PATH, sim_runner, protocol)
    pathway.pairs = [(CircuitNodeId(id=1, population="population"), CircuitNodeId(id=2, population="population"))]
    pathway.pre_syn_type = 'EXC'
    pathway.min_ampl = 12.3
    pathway.t_stim = 199.
    pathway.trace_filters = [SpikeFilter(t_start=0, v_max=100)]
    return pathway


def test__init_traces_dump():
    with TemporaryDirectory('test-init-traces-dump') as folder:
        pathway = _dummy_pathway(dict(dump_traces=False, output_dir=folder))
        traces_path = pathway._init_traces_dump()

        with h5py.File(traces_path, 'r') as h5f:
            assert h5f.attrs['data'] == 'voltage'

    with TemporaryDirectory('test-init-traces-dump') as folder:
        pathway = _dummy_pathway(dict(dump_traces=True, output_dir=folder, clamp='voltage'))
        traces_path = pathway._init_traces_dump()

        with h5py.File(traces_path, 'r') as h5f:
            assert h5f.attrs['data'] == 'current'


def test__run_one_pair():
    all_amplitudes = list()

    with TemporaryDirectory('test-run-one-pair') as folder:
        pathway = _dummy_pathway(dict(output_dir=folder))

        h5_file = os.path.join(folder, 'dump.h5')
        pathway._run_one_pair(
            (CircuitNodeId(id=1, population="population"), CircuitNodeId(id=2, population="population")), 
            all_amplitudes, 
            h5_file
        )
        assert_allclose(all_amplitudes, [94.0238021084036])

        with h5py.File(h5_file, 'r') as f:
            assert '/traces/population_1-population_2' in f
            group = f['/traces/population_1-population_2']
            assert group.attrs['pre_id'] == 1
            assert group.attrs['pre_population'] == "population"
            assert group.attrs['post_id'] == 2
            assert group.attrs['post_population'] == "population"
            assert 'trials' in group
            assert 'average' in group


def test__run_pathway_no_pairs():
    with TemporaryDirectory('test-run-pathway') as folder:
        pathway = _dummy_pathway(dict(output_dir=folder))
        pathway.pairs = []
        pathway.run()

        assert_array_equal(os.listdir(folder), ['pathway.traces.h5'])

        with h5py.File(os.path.join(folder, 'pathway.traces.h5'), 'r') as f:
            assert_array_equal(list(f.keys()), [])


def test__run_pathway():
    with TemporaryDirectory('test-run-pathway-dump-trace') as folder:
        pathway = _dummy_pathway(dict(dump_traces=True, output_dir=folder))
        pathway.run()

        assert_array_equal(list(sorted(os.listdir(folder))),
                           ['pathway.amplitudes.txt', 'pathway.summary.yaml', 'pathway.traces.h5'])
        with h5py.File(os.path.join(folder, 'pathway.traces.h5'), 'r') as f:
            assert_array_equal(list(f['traces']['population_1-population_2'].keys()), ['average', 'trials'])

    with TemporaryDirectory('test-run-pathway-no-traces') as folder:
        pathway = _dummy_pathway(dict(dump_traces=False, output_dir=folder))
        pathway.run()
        assert_array_equal(list(sorted(os.listdir(folder))),
                           ['pathway.amplitudes.txt', 'pathway.summary.yaml'])


def test__get_reference_and_scaling():
    pathway = _dummy_pathway({})
    model_mean = 33.3
    params = {}
    pathway.config = {'reference': {'psp_amplitude': {'mean': 12}}, 'protocol': {'hold_V': 43.0}}
    reference, scaling = pathway._get_reference_and_scaling(model_mean, params)
    assert reference == {'mean': 12}
    assert_allclose(scaling, 0.11275791920953214)

    def pathway_null_hold_V(folder):
        '''A helper to test a pathway with null hold_V'''
        pathway = _dummy_pathway(dict(dump_traces=False, dump_amplitudes=False, output_dir=folder))
        pathway.config['protocol']['hold_V'] = None
        # let's have 2 pairs so averaging of resting potential does something
        pathway.pairs = [(1, 2), (3, 4)]
        pathway.t_stim = 1200
        return pathway

    with TemporaryDirectory('test-scaling-null-hold-v-ok') as folder:
        pathway = pathway_null_hold_V(folder)

        # Required to fill Pathway.resting_potential array
        pathway.run()

        reference, scaling = pathway._get_reference_and_scaling(model_mean, params)
        assert_allclose(scaling, 0.007170083739722974)
