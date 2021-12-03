import numpy as np
import pandas as pd
from numpy.testing import assert_array_equal
from unittest.mock import MagicMock, patch
import psp_validation.cv_validation.setsim as test_module


def test_is_valid_connection():

    def get_mock_circuit(return_value):
        # Basically makes circuit.cells.get() return pd.DataFrame(return_value)
        return MagicMock(cells=MagicMock(
            get=MagicMock(return_value=pd.DataFrame(return_value))))

    constraints = [100, 100, 100]

    # Testing for return values less than constraints distance away
    value = np.random.random((2, 3)) * 1000
    value[1, :] = value[0, :] + [75, 25, 40]
    assert test_module.is_valid_connection(None, get_mock_circuit(value), constraints)

    # Testing for return values 1 or more over the limit
    value[1, :] = value[0, :] + [75, 25, 140]
    assert not test_module.is_valid_connection(None, get_mock_circuit(value), constraints)
    value[1, :] = value[0, :] + [75, 125, 140]
    assert not test_module.is_valid_connection(None, get_mock_circuit(value), constraints)
    value[1, :] = value[0, :] + [175, 125, 140]
    assert not test_module.is_valid_connection(None, get_mock_circuit(value), constraints)


def test_get_pairs():

    pairs = list('abcdefghijklmn')
    circuit = MagicMock(connectome=MagicMock(iter_connections=MagicMock(return_value=pairs)))
    targets = pathway = MagicMock()

    # Mainly testing that the function returns the correct amount of pairs
    with patch('psp_validation.cv_validation.setsim.is_valid_connection') as patched:
        patched.return_value = True

        for i in range(10):
            assert_array_equal(test_module.get_pairs(circuit, pathway, targets, i),
                               pairs[:i])
