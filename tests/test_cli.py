import os
from click.testing import CliRunner
from psp_validation.cli import run, plot

from .utils import TEST_DATA_DIR_PSP

DATA = TEST_DATA_DIR_PSP/ "simple"


def test_cli(tmp_path):
    runner = CliRunner()
    folder = tmp_path / "test-psp-cli"

    result = runner.invoke(run,
                            ['-c', str(DATA / 'simulation_config.json'),
                            '-o', folder,
                            '-t', str(DATA / 'usecases/hippocampus/targets.yaml'),
                            '-e', 'default',
                            '-n', '1',
                            '-r', '1',
                            '-j', '1',
                            str(DATA / 'usecases/hippocampus/pathways/SP_PVBC-SP_PC.yaml'),
                            '--dump-traces',
                            '--dump-amplitudes'])

    assert result.exit_code == 0, result.exc_info
    assert {path.name for path in folder.iterdir()} == {
        'SP_PVBC-SP_PC.traces.h5',
        'SP_PVBC-SP_PC.summary.yaml',
        'SP_PVBC-SP_PC.amplitudes.txt',
    }


def test_plot_cli(tmp_path):
    runner = CliRunner()

    runner.invoke(plot,
                  [str(TEST_DATA_DIR_PSP / 'small-traces.h5'), '-o', tmp_path])

    assert os.listdir(tmp_path) == ['small-traces']
    out_folder = os.path.join(tmp_path, 'small-traces')
    assert os.listdir(out_folder) == ['All-11085-All-10126.png']
