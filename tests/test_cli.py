from pathlib import Path
from tempfile import TemporaryDirectory
import os
from os.path import dirname
from click.testing import CliRunner
from psp_validation.cli import run, plot

DATA = Path(__file__).parent / 'input_data'


def test_cli():
    runner = CliRunner()
    input_folder = DATA / 'simple'
    # go to BlueConfig dir to run the simu
    orig_path = Path(os.curdir).resolve()
    os.chdir(input_folder)
    try:
        with TemporaryDirectory('test-psp-cli') as folder:
            result = runner.invoke(run,
                                   ['-c', 'BlueConfig',
                                    '-o', folder,
                                    '-t', 'usecases/hippocampus/targets.yaml',
                                    '-n', '1',
                                    '-r', '1',
                                    '-j', '1',
                                    'usecases/hippocampus/pathways/SP_PVBC-SP_PC.yaml',
                                    '--dump-traces',
                                    '--dump-amplitudes'])

            assert result.exit_code == 0, result.exc_info
            assert {path.name for path in Path(folder).iterdir()} == {
                'SP_PVBC-SP_PC.traces.h5',
                'SP_PVBC-SP_PC.summary.yaml',
                'SP_PVBC-SP_PC.amplitudes.txt',
            }
    finally:
        os.chdir(orig_path)


def test_plot_cli():
    runner = CliRunner()

    with TemporaryDirectory('test-psp-plot-cli') as folder:
        runner.invoke(plot,
                      [os.path.join(dirname(__file__), 'small-traces.h5'), '-o', folder])

        assert os.listdir(folder) == ['small-traces']
        out_folder = os.path.join(folder, 'small-traces')
        assert os.listdir(out_folder) == ['a11086-a10127.png']
