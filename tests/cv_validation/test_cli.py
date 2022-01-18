import os
from pathlib import Path
from tempfile import TemporaryDirectory
from click.testing import CliRunner

import psp_validation.cv_validation.cli as test_module

DATA = Path(__file__).parent / 'input_data'
PATHWAY = DATA / 'SP_PVBC-SP_PC.yaml'
TARGETS = DATA / 'targets.yaml'
CIRCUIT = '/gpfs/bbp.cscs.ch/project/proj42/circuits/CA1.O1/20190306.syn/CircuitConfig'


def _test_setup(folder):
    runner = CliRunner()

    result = runner.invoke(test_module.setup,
                           ['-c', CIRCUIT,
                            '-o', folder,
                            '-t', TARGETS,
                            '-p', PATHWAY,
                            '-n', '2',
                            '--seed', '100'])

    assert result.exit_code == 0, result.output

    sim_dir = Path(folder) / 'simulations'
    assert sim_dir.exists()
    assert (sim_dir / 'pairs.csv').exists()
    assert (sim_dir / 'BlueConfig').exists()


def _test_simulation(folder):
    runner = CliRunner()

    result = runner.invoke(test_module.run,
                           ['-o', folder,
                            '-p', PATHWAY,
                            '-r', '2',
                            '--nrrp', '1', '2',
                            '-j', '4'])

    assert result.exit_code == 0, result.output

    sim_dir = Path(folder) / 'simulations'
    assert (sim_dir / 'simulation_nrrp1.h5').exists()
    assert (sim_dir / 'simulation_nrrp2.h5').exists()


def _test_analysis(folder):
    runner = CliRunner()

    result = runner.invoke(test_module.calibrate,
                           ['-o', folder,
                            '-p', PATHWAY,
                            '-r', '10',
                            '-n', '1',
                            '--nrrp', '1', '2',
                            '-j', '2'])

    assert result.exit_code == 0, result.output

    fig_dir = Path(folder) / 'figures'
    assert fig_dir.exists()
    assert (fig_dir / 'SP_PVBC-SP_PC_CV_regression.png').exists()
    assert (fig_dir / 'SP_PVBC-SP_PC_lambdas.png').exists()


def test_workflow(tmp_path):
    # Run the whole workflow to not have to store data in GitLab
    _test_setup(tmp_path)
    _test_simulation(tmp_path)
    _test_analysis(tmp_path)
