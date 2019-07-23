import os
import numpy as np
import shutil
import tempfile
from contextlib import contextmanager


@contextmanager
def setup_tempdir(prefix, cleanup=True):
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    try:
        yield temp_dir
    finally:
        if cleanup:
            shutil.rmtree(temp_dir)


def mock_run_pair_simulation_suite(*args, **kwargs):
    filename = os.path.join(os.path.dirname(__file__), 'input_data', 'example_trace.txt')
    data = np.loadtxt(filename)
    time = data[:, 0]
    voltage = data[:, 1]
    trace = (voltage, time)
    return [trace]
