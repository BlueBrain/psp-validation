from pathlib import Path

import pandas as pd
import numpy as np
from numpy.testing import assert_almost_equal

import psp_validation.simulation as test_module

DATA = Path(__file__).parent / 'cv_validation' / 'input_data'


def test_run_pair_simulation_clamp_current():
    config = str(DATA / 'BlueConfig')
    pair_df = pd.read_csv(DATA / 'pairs.csv')
    _, time, _, voltage = test_module.run_pair_simulation(
            blue_config=config,
            pre_gid=pair_df.pre[0],
            post_gid=pair_df.post[0],
            base_seed=pair_df.seed[0],
            record_dt=None,  # Use what's in BlueConfig
            nrrp=1,
            hold_V=-73.0,
            hold_I=0.02,
            t_stim=800.0,
            t_stop=1000.0)

    assert_almost_equal(time, np.arange(0.0, 1000.01, 0.025))

    # Check a few data points, acquired with supposedly working solution
    # expected = [-73, -68.1933138, -69.9867907, -69.9858326]  # with bglibpy 4.7.15
    expected = [-73, -68.1933138, -69.9867907, -69.9858781]  # with bglibpy 4.7.16
    assert_almost_equal(voltage[[0, 1000, 20000, -1]], expected)


def test_run_pair_simulation_clamp_voltage():
    config = str(DATA / 'BlueConfig')
    pair_df = pd.read_csv(DATA / 'pairs.csv')
    _, time, current, voltage = test_module.run_pair_simulation(
            blue_config=config,
            pre_gid=pair_df.pre[0],
            post_gid=pair_df.post[0],
            base_seed=pair_df.seed[0],
            record_dt=None,  # Use what's in BlueConfig
            nrrp=1,
            hold_V=-73.0,
            t_stim=800.0,
            t_stop=1000.0)

    assert_almost_equal(time, np.arange(0.0, 1000.01, 0.025))

    # Check a few data points, acquired with supposedly working solution
    assert_almost_equal(current[[0, 1000, 20000, -1]],
                        [0, -0.0739914, -0.0609556, -0.0609568])
