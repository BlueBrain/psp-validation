import pathlib
from itertools import repeat

import numpy as np

from psp_validation.simulation import SimulationResult

TEST_DATA_DIR_PSP = pathlib.Path(__file__).parent / "input_data"
TEST_DATA_DIR_CV = pathlib.Path(__file__).parent / "cv_validation" / "input_data"


def _make_traces(vss, ts):
    return list(zip(vss, repeat(ts)))


def mock_run_pair_simulation_suite(*_, **__):
    filename = TEST_DATA_DIR_PSP / "example_trace.txt"
    data = np.loadtxt(filename)
    time = data[:, 0]
    voltage = data[:, 1]
    return SimulationResult({"e_GABAA": -90}, time, [voltage], [voltage])
