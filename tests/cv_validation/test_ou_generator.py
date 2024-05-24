from unittest.mock import patch

import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_equal

import psp_validation.cv_validation.ou_generator as test_module

TEST_TAU = 28.2
TEST_SIGMA = 0.22


@patch.object(test_module, "ou_generator")
def test_add_ou_noise(mock_generator):
    t = np.arange(0, 100, 0.1)
    traces = np.full((2, len(t)), -50.0)
    noise = np.random.random(t.shape[0])

    mock_generator.return_value = noise
    res = test_module.add_ou_noise(t, traces.copy(), TEST_TAU, TEST_SIGMA)
    assert_array_equal(res, traces + noise)


def test_ou_generator():
    t = np.arange(0, 1, 0.1)

    np.random.seed(1)
    res = test_module.ou_generator(t, TEST_TAU, TEST_SIGMA, 0)

    # expected values acquired with the initial code before any modifications
    expected = np.array(
        [
            0.0,
            0.030095,
            0.018654,
            0.008802,
            -0.011108,
            0.004965,
            -0.037694,
            -0.005234,
            -0.019318,
            -0.013339,
        ],
        dtype=np.float32,
    )
    assert_array_almost_equal(res, expected)
