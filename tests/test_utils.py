import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_equal

import psp_validation.utils as test_module


def _simple_generator(x_array):
    for x in x_array:
        yield x

@pytest.mark.parametrize('expected', [[1, 2.2]])
@pytest.mark.parametrize('iterable_fun', [np.array,
                                          pd.Series,
                                          set,
                                          tuple,
                                          _simple_generator,
                                          ])
def test_ensure_list_from_iterables(expected, iterable_fun):

    assert_array_equal(expected,
                       test_module.ensure_list(iterable_fun(expected)))

@pytest.mark.parametrize('scalar_value', [1,
                                          1.1,
                                          np.pi,
                                          np.Infinity,
                                          np.nan,
                                          'c',
                                          'str',
                                          None,
                                          ])
def test_ensure_list_from_scalars(scalar_value):

    assert_array_equal([scalar_value],
                       test_module.ensure_list(scalar_value))

