import os

from psp_validation import psp

from tests.utils import TEST_DATA_DIR_PSP


def test_run(tmp_path):
    input_folder = TEST_DATA_DIR_PSP / "simple"

    psp.run(
        [input_folder / "usecases/hippocampus/pathways/SP_PVBC-SP_PC.yaml"],
        input_folder / "simulation_config.json",
        input_folder / "usecases/hippocampus/targets.yaml",
        tmp_path,
        num_pairs=1,
        num_trials=1,
        edge_population="default",
        clamp="current",
        dump_traces=True,
        dump_amplitudes=True,
        seed=0,
        jobs=1,
    )
    assert {*os.listdir(tmp_path)} == {
        "SP_PVBC-SP_PC.traces.h5",
        "SP_PVBC-SP_PC.summary.yaml",
        "SP_PVBC-SP_PC.amplitudes.txt",
    }
