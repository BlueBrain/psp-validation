import os
from os.path import dirname

from mock import MagicMock, patch
from nose.tools import (assert_almost_equal, assert_dict_equal, assert_equal,
                        assert_raises, assert_true, ok_, raises)

from psp_validation import psp

from .utils import mock_run_pair_simulation_suite, setup_tempdir

_bconfig = "psp_validation/tests/input_data/sim_tencell_example1/RefBlueConfig_Scaling"

_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_data")


@patch('psp_validation.psp.run_pair_simulation_suite',
       return_value=mock_run_pair_simulation_suite())
@patch('psp_validation.pathways._get_pathway_pairs', side_effect=lambda *args, **kargs: [(14194, 14494)])
@patch('psp_validation.psp.bluepy.Circuit')
@patch('psp_validation.pathways.get_synapse_type', return_value='EXC')
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
