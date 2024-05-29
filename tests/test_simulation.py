import numpy as np
import pandas as pd
import pytest
from bluepysnap.circuit_ids import CircuitNodeId
from numpy.testing import assert_almost_equal

import psp_validation.simulation as test_module

from tests.utils import PROJ12_ACCESS, TEST_DATA_DIR_CV, TEST_DATA_DIR_PSP

SIMULATION_CONFIG = str(TEST_DATA_DIR_PSP / "simple" / "simulation_config.json")
PAIRS = str(TEST_DATA_DIR_CV / "pairs.csv")


@pytest.mark.skipif(not PROJ12_ACCESS, reason="No access to proj12")
def test_run_pair_simulation_clamp_current():
    pair_df = pd.read_csv(PAIRS)
    _, time, _, voltage = test_module.run_pair_simulation(
        sonata_simulation_config=SIMULATION_CONFIG,
        pre_gid=CircuitNodeId(id=pair_df.pre_id[0], population=pair_df.pre_population[0]),
        post_gid=CircuitNodeId(id=pair_df.post_id[0], population=pair_df.post_population[0]),
        base_seed=pair_df.seed[0],
        record_dt=None,  # Use what's in BlueConfig
        nrrp=1,
        hold_V=-73.0,
        hold_I=0.02,
        t_stim=800.0,
        t_stop=1000.0,
    )

    assert_almost_equal(time, np.arange(0.0, 1000.01, 0.025))

    # Check a few data points, acquired with supposedly working solution
    # expected = [-73, -68.1933138, -69.9867907, -69.9858326]  # with bglibpy 4.7.15
    # expected = [-73, -68.1933138, -69.9867907, -69.9858781]  # with bglibpy 4.7.16
    # expected = [-73, -68.1933134, -69.9867904, -69.9858778]  # with neuron 8.2.1 in a virtualenv

    # with bluecellulab 2.5.7 (recalculating afferent_section_pos)
    # expected = [-73, -68.1933134, -69.9867904, -69.9856424]

    # with bluecellulab 2.6.2 using afferent_section_pos from h5
    # expected = [-73, -68.1933134, -69.9867904, -69.9856456]

    expected = [-73, -68.1933134, -69.9867904, -69.9856424]  # with bluecellulab 2.6.15

    assert_almost_equal(voltage[[0, 1000, 20000, -1]], expected)


@pytest.mark.skipif(not PROJ12_ACCESS, reason="No access to proj12")
def test_run_pair_simulation_clamp_voltage():
    pair_df = pd.read_csv(PAIRS)
    _, time, current, _ = test_module.run_pair_simulation(
        sonata_simulation_config=SIMULATION_CONFIG,
        pre_gid=CircuitNodeId(id=pair_df.pre_id[0], population=pair_df.pre_population[0]),
        post_gid=CircuitNodeId(id=pair_df.post_id[0], population=pair_df.post_population[0]),
        base_seed=pair_df.seed[0],
        record_dt=None,  # Use what's in BlueConfig
        nrrp=1,
        hold_V=-73.0,
        t_stim=800.0,
        t_stop=1000.0,
    )

    assert_almost_equal(time, np.arange(0.0, 1000.01, 0.025))

    # Check a few data points, acquired with supposedly working solution
    # expected = [0, -0.0739914, -0.0609556, -0.0609568]  # with bglibpy

    # with bluecellulab 2.5.7
    expected = [0, -0.0739914, -0.0609556, -0.0609562]

    assert_almost_equal(current[[0, 1000, 20000, -1]], expected)
