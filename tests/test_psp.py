import os
from pathlib import Path
from tempfile import TemporaryDirectory

from psp_validation import psp

DATA = Path(__file__).parent / 'input_data'


def test_run():
    input_folder = DATA / 'simple'

    # go to data dir to run the simulation
    orig_path = Path(os.curdir).resolve()
    os.chdir(input_folder)
    try:
        with TemporaryDirectory('test-psp-run') as folder:
            psp.run(
                ['usecases/hippocampus/pathways/SP_PVBC-SP_PC.yaml'],
                'simulation_config.json',
                'usecases/hippocampus/targets.yaml',
                folder,
                num_pairs=1,
                num_trials=1,
                clamp='current',
                dump_traces=True,
                dump_amplitudes=True,
                seed=0,
                jobs=1,
            )
            assert {path.name for path in Path(folder).iterdir()} == {
                'SP_PVBC-SP_PC.traces.h5',
                'SP_PVBC-SP_PC.summary.yaml',
                'SP_PVBC-SP_PC.amplitudes.txt',
            }
    finally:
        os.chdir(orig_path)
