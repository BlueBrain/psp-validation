from pathlib import Path

import pandas as pd
import numpy as np
from numpy.testing import assert_almost_equal
from bluepysnap.circuit_ids import CircuitNodeId

import psp_validation.simulation as test_module

SONATA_DATA = Path(__file__).parent / 'input_data' / "simple"
DATA = Path(__file__).parent / 'cv_validation' / 'input_data'


def test_run_pair_simulation_clamp_current():
    config = str(SONATA_DATA / 'simulation_config.json')
    pair_df = pd.read_csv(DATA / 'pairs.csv')
    _, time, _, voltage = test_module.run_pair_simulation(
                sonata_simulation_config=config,
                pre_gid=CircuitNodeId(id=pair_df.pre_id[0], population=pair_df.pre_population[0]),
                post_gid=CircuitNodeId(id=pair_df.post_id[0], population=pair_df.post_population[0]),
                base_seed=pair_df.seed[0],
                record_dt=None,  # Use what's in BlueConfig
                nrrp=1,
                hold_V=-73.0,
                hold_I=0.02,
                t_stim=800.0,
                t_stop=1000.0)

    assert_almost_equal(time, np.arange(0.0, 1000.01, 0.025))

    # Check a few data points, acquired with supposedly working solution
    expected = [-73.        , -76.644092  , -75.52728681, -75.52716122]
    assert_almost_equal(voltage[[0, 1000, 20000, -1]], expected)


def test_run_pair_simulation_clamp_voltage():
    config = str(SONATA_DATA / 'simulation_config.json')
    pair_df = pd.read_csv(DATA / 'pairs.csv')
    _, time, current, voltage = test_module.run_pair_simulation(
            sonata_simulation_config=config,
            pre_gid=CircuitNodeId(id=pair_df.pre_id[0], population=pair_df.pre_population[0]),
            post_gid=CircuitNodeId(id=pair_df.post_id[0], population=pair_df.post_population[0]),
            base_seed=pair_df.seed[0],
            record_dt=None,  # Use what's in BlueConfig
            nrrp=1,
            hold_V=-73.0,
            t_stim=800.0,
            t_stop=1000.0)

    assert_almost_equal(time, np.arange(0.0, 1000.01, 0.025))

    # Check a few data points, acquired with supposedly working solution
    assert_almost_equal(current[[0, 1000, 20000, -1]],
                        [0.       , 0.0714614, 0.0655304, 0.065529 ])
