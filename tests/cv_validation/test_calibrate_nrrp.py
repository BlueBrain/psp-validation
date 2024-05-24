from unittest.mock import Mock, patch

import numpy as np
from numpy.testing import assert_almost_equal, assert_array_equal

import psp_validation.cv_validation.calibrate_nrrp as test_module


def test__sample_cvs():
    np.random.seed(1)
    nrrps = [1, 2]
    counts = [2, 3]
    cvs = {f"nrrp{i}": {"CV": np.arange(5), "JK_CV": np.arange(5)} for i in range(1, 3)}

    res = test_module._sample_cvs(nrrps, counts, cvs)
    assert_array_equal(res, [1.8, 1.2])


@patch.object(test_module, "_sample_cvs", new=Mock(return_value=(0, 1)))
def test_scan_lambdas():
    np.random.seed(1)
    res = test_module.scan_lambdas(None, [1, 2], 1, 1)

    # These values are just simply copied from the original output before changes
    assert_array_equal(res[0], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2])
    assert_array_equal(res[1], np.zeros(11))
    assert_array_equal(res[2], np.ones(11))


def test__flatten_cvs():
    cvs = {f"nrrp{i}": {"CV": [i], "JK_CV": [-i]} for i in range(1, 10)}
    res = test_module._flatten_cvs(cvs, [1, 9])

    assert_array_equal(res[0], range(1, 10))
    assert_array_equal(res[1], range(-1, -10, -1))


def test_regress_cvs():
    np.random.seed(1)

    cvs = np.arange(100)
    jk_cvs = 2 * cvs + np.random.normal(size=100) + 3
    target = 50

    res = test_module.regress_cvs(cvs, jk_cvs, target)
    assert_almost_equal(res[0], 103.06225378)


def test_regress_lambdas():
    lambdas = np.arange(100, 120)
    target_cv = 2.5 + np.random.random()
    target_jk_cv = 9.5 + np.random.random()
    cvs = np.arange(0, 20)
    jk_cvs = np.arange(0, 20)

    res = test_module.regress_lambdas(lambdas, cvs, target_cv, jk_cvs, target_jk_cv)
    assert_array_equal(res, [103, 110])

    target_cv = cvs[-1] + 1
    target_jk_cv = jk_cvs[-1] + 1
    res = test_module.regress_lambdas(lambdas, cvs, target_cv, jk_cvs, target_jk_cv)
    assert_array_equal(res, [None, None])
