from mock import patch
import os
from os.path import dirname
from nose.tools import assert_equal, ok_
from click.testing import CliRunner
from psp_validation.cli import cli

from .utils import setup_tempdir, mock_run_pair_simulation_suite

_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_data")

@patch('psp_validation.psp.run_pair_simulation_suite', return_value=mock_run_pair_simulation_suite())
@patch('psp_validation.pathways._get_pathway_pairs', side_effect=lambda *args, **kargs: [(14194, 14494)])
@patch('psp_validation.psp.bluepy.Circuit')
@patch('psp_validation.pathways.get_synapse_type', return_value='EXC')
def test_cli(m1, m2, m3, m4):
    runner = CliRunner()
    hippo_path = os.path.join(dirname(__file__), '..', 'usecases', 'hippocampus')

    with setup_tempdir('test-psp-cli') as folder:
        runner.invoke(cli,
                      ['run',
                       '-c', os.path.join(dirname(__file__), 'input_data', 'Ref_BlueConfig'),
                       '-o', folder,
                       '-t', os.path.join(hippo_path, 'targets.yaml'),
                       '-n', '1',
                       '-r', '1',
                       '-j', '1',
                       os.path.join(_path, 'pathway.yaml'),
                       '--dump-traces',
                       '--dump-amplitudes'])

        ok_(os.path.exists(os.path.join(folder, 'pathway.summary.yaml')))
