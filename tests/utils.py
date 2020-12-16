import os
import numpy as np
from itertools import repeat

from psp_validation.simulation import SimulationResult


def _make_traces(vss, ts):
    return list(zip(vss, repeat(ts)))


def mock_run_pair_simulation_suite(*args, **kwargs):
    filename = os.path.join(os.path.dirname(__file__), 'input_data', 'example_trace.txt')
    data = np.loadtxt(filename)
    time = data[:, 0]
    voltage = data[:, 1]
    return SimulationResult({'e_GABAA': -90}, time, [voltage], [voltage])
