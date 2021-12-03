from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import numpy as np
from numpy.testing import assert_almost_equal

import psp_validation.cv_validation.simulator as test_module

DATA = Path(__file__).parent / 'input_data'


def test__get_hsynapse_attributes():
    np.random.seed(42)

    class MockHSynapse():
        def __init__(self):
            self.Nrrp = 1
            self.Use = np.round(np.random.random(), decimals=2)
            self.Fake = '3'

    synapses = [Mock(hsynapse=MockHSynapse()) for _ in range(5)]
    res = test_module._get_hsynapse_attributes(synapses)
    assert res == {'Nrrp': 5 * [1], 'Use': [0.37, 0.95, 0.73, 0.6, 0.16]}


def test_run_sim():
    config = DATA / 'BlueConfig'
    pair_df = pd.read_csv(DATA / 'pairs.csv')
    time, soma = test_module.run_sim(pair_df.seed[0],
                                     DATA,
                                     pair_df.pre[0],
                                     pair_df.post[0],
                                     1,
                                     800.0)

    assert_almost_equal(time, np.arange(0.025, 1000.01, 0.025))

    # Check a few data points
    assert_almost_equal(soma[[0, 1000, 20000, -1]],
                        [-58.58385418, -76.45452019, -70.72049316, -70.71840202])
