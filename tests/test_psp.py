import os
from pathlib import Path
from tempfile import TemporaryDirectory
import warnings

from nose.tools import (assert_almost_equal, assert_dict_equal, assert_equal,
                        assert_raises, assert_true, ok_, raises)

from psp_validation import psp

DATA = Path(__file__).parent / 'input_data'


def test_run():
    input_folder = DATA / 'simple'

    # go to BlueConfig dir to run the simu
    orig_path = Path(os.curdir).resolve()
    os.chdir(input_folder)
    try:
        with TemporaryDirectory('test-psp-run') as folder:
            with warnings.catch_warnings(record=True) as w:
                psp.run(
                    ['usecases/hippocampus/pathways/SP_PVBC-SP_PC.yaml'],
                    'BlueConfig',
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
                assert_equal(len(w), 1)
                ok_("ForwardSkip found in config file but will disabled for this simulation. (SSCXDIS-229)"
                    in str(w[-1].message))
            assert_equal({path.name for path in Path(folder).iterdir()},
                         {'SP_PVBC-SP_PC.traces.h5',
                          'SP_PVBC-SP_PC.summary.yaml',
                          'SP_PVBC-SP_PC.amplitudes.txt'})
    finally:
        os.chdir(orig_path)
