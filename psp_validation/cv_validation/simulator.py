"""
Single cell sim in bluecellulab for NRRP calibaration
author: Giuseppe Chindemi (03.2020)
+ minor modifications by András Ecker for bluecellulab compatibility (02.2021)
"""

import logging
import os
import time

import h5py
import joblib
import numpy as np
from bluepysnap.circuit_ids import CircuitNodeId

from psp_validation.simulation import get_holding_current, run_pair_simulation
from psp_validation.utils import ensure_list, isolate

L = logging.getLogger(__name__)


def run_sim_handler(
    sonata_simulation_config, input_params, nrrp, protocol, seeds, clamp, n_jobs=None
):
    """apply func to all items in it, using a process pool"""
    t_stim = protocol['t_stim']
    hold_V = protocol['hold_V']

    if clamp == 'current':
        hold_I = get_holding_current(
            log_level=100,
            hold_V=hold_V,
            post_gid=CircuitNodeId(
                id=input_params.post_id,
                population=input_params.post_population,
            ),
            sonata_simulation_config=sonata_simulation_config,
            post_ttx=False
        )
    else:
        hold_I = None

    if n_jobs is None:
        n_jobs = 1
    elif n_jobs <= 0:
        n_jobs = -1

    worker = joblib.delayed(isolate(run_pair_simulation))
    results = joblib.Parallel(n_jobs=n_jobs, backend='loky')([
        worker(
            sonata_simulation_config=sonata_simulation_config,
            pre_gid=CircuitNodeId(
                id=input_params.pre_id,
                population=input_params.pre_population,
            ),
            post_gid=CircuitNodeId(
                id=input_params.post_id,
                population=input_params.post_population,
            ),
            t_stop=t_stim + 200,
            t_stim=t_stim,
            hold_I=hold_I,
            hold_V=hold_V,
            record_dt=None,
            base_seed=seed,
            nrrp=nrrp,
            log_level=L.getEffectiveLevel()
        )
        for seed in seeds
    ])

    # return only time, current and voltage for each simulation
    return [r[1:] for r in results]


def run_simulation(input_params, num_trials, nrrp, protocol, out_dir, clamp='current', n_jobs=None):
    """Run the simulation with the provided arguments.

    Args:
        input_params: one row in pandas DF containing seed, pre, post
        num_trials: number of repetitions per pair
        nrrp: nrrp value to simulate
        protocol: dictionary containing the protocol configuration as defined in a pathway file
        out_dir: path to the output directory
        clamp: clamping to apply (either 'current' or 'voltage')
        n_jobs: number of parallel jobs
    """
    # TODO: Fix "too-many-locals" in the next iteration
    # pylint: disable=too-many-locals
    assert clamp in ('current', 'voltage')
    L.info("Starting simulation")

    # Set base seed
    np.random.seed(input_params.seed)

    # Get runtime seeds
    seeds = np.random.randint(1, 99999999 + 1, size=num_trials)

    # Create results HDF5 database
    with h5py.File(os.path.join(out_dir, f"simulation_nrrp{nrrp}.h5"), "a") as h5_file:
        h5_file.attrs.create('clamp', clamp)
        pair_group = h5_file.create_group(
            f"{input_params.pre_population}-{input_params.pre_id}"
            f"_{input_params.post_population}-{input_params.post_id}"
        )
        pair_group.attrs.create("base_seed", input_params.seed)

        # Run sweeps
        start_time = time.perf_counter()
        L.debug("### DEBUG MODE ###")
        time_current_voltage = run_sim_handler(os.path.join(out_dir, 'sonata_config.json'),
                                               input_params,
                                               nrrp,
                                               protocol,
                                               seeds,
                                               clamp,
                                               n_jobs=n_jobs)
        for _seed, (time_, current, voltage) in zip(seeds, time_current_voltage):
            seed_group = pair_group.create_group(f"seed{_seed}")
            seed_group.create_dataset("time", data=time_, chunks=True,
                                      compression="gzip", compression_opts=9)
            seed_group.create_dataset("soma_voltage", data=voltage, chunks=True,
                                      compression="gzip", compression_opts=9)
            seed_group.create_dataset("soma_current", data=ensure_list(current), chunks=True,
                                      compression="gzip", compression_opts=9)
        L.info("Elapsed time: %.2f", (time.perf_counter() - start_time))

    L.info("All done")
