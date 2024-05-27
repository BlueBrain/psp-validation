"""Single cell sim in bluecellulab for NRRP calibration

author: Giuseppe Chindemi
+ minor modifications by András Ecker for bluecellulab compatibility
"""

import logging
import time

import h5py
import joblib
import numpy as np
from bluepysnap.circuit_ids import CircuitNodeId

from psp_validation import PSPError
from psp_validation.simulation import get_holding_current, run_pair_simulation
from psp_validation.utils import ensure_list, isolate

L = logging.getLogger(__name__)
DOC_REF = (
    "https://bbpteam.epfl.ch/documentation/projects/psp-validation/latest/"
    "files.html#simulation-parameters"
)


def _resolve_holding_current(hold_v, post_gid, simulation_config, post_ttx):
    if hold_v is None:
        L.warning(f"'hold_V' is None. 'hold_I' will be set to 0. See: {DOC_REF}")
        return 0

    return get_holding_current(
        log_level=100,
        hold_V=hold_v,
        post_gid=post_gid,
        sonata_simulation_config=simulation_config,
        post_ttx=post_ttx,
    )


def resolve_holding_current_and_voltage(
    protocol, clamp, post_gid, simulation_config, post_ttx=None
):
    """Resolve the holding current and voltage based on the config."""
    if ("hold_V" in protocol) == ("hold_I" in protocol):
        raise PSPError(f"Either 'hold_V' or 'hold_I' should be specified. See: {DOC_REF}")

    if clamp == "current":
        if "hold_I" in protocol:
            hold_i = protocol["hold_I"]
            hold_v = None
        else:
            hold_v = protocol["hold_V"]
            hold_i = _resolve_holding_current(hold_v, post_gid, simulation_config, post_ttx)
    else:
        hold_i = None
        hold_v = protocol["hold_V"]

    return hold_i, hold_v


def run_sim_handler(
    sonata_simulation_config, input_params, nrrp, protocol, seeds, clamp, n_jobs=None
):
    """Apply func to all items in it, using a process pool"""
    t_stim = protocol["t_stim"]
    post_gid = CircuitNodeId(id=input_params.post_id, population=input_params.post_population)

    hold_i, hold_v = resolve_holding_current_and_voltage(
        protocol, clamp, post_gid, sonata_simulation_config
    )

    if n_jobs is None:
        n_jobs = 1
    elif n_jobs <= 0:
        n_jobs = -1

    worker = joblib.delayed(isolate(run_pair_simulation))
    results = joblib.Parallel(n_jobs=n_jobs, backend="loky")(
        [
            worker(
                sonata_simulation_config=sonata_simulation_config,
                pre_gid=CircuitNodeId(
                    id=input_params.pre_id,
                    population=input_params.pre_population,
                ),
                post_gid=post_gid,
                t_stop=t_stim + 200,
                t_stim=t_stim,
                hold_I=hold_i,
                hold_V=hold_v,
                record_dt=None,
                base_seed=seed,
                nrrp=nrrp,
                log_level=L.getEffectiveLevel(),
            )
            for seed in seeds
        ],
    )

    # return only time, current and voltage for each simulation
    return [r[1:] for r in results]


def run_simulation(
    simulation, input_params, num_trials, nrrp, protocol, out_dir, clamp="current", n_jobs=None
):
    """Run the simulation with the provided arguments.

    Args:
        simulation: path to Sonata simulation config
        input_params: one row in pandas dataframe containing seed, pre, post
        num_trials: number of repetitions per pair
        nrrp: nrrp value to simulate
        protocol: dictionary containing the protocol configuration as defined in a pathway file
        out_dir: path to the output directory
        clamp: clamping to apply (either 'current' or 'voltage')
        n_jobs: number of parallel jobs
    """
    assert clamp in {"current", "voltage"}
    L.info("Starting simulation")

    # Set base seed
    np.random.seed(input_params.seed)

    # Get runtime seeds
    seeds = np.random.randint(1, 99999999 + 1, size=num_trials)

    # Create results HDF5 database
    with h5py.File(out_dir / f"simulation_nrrp{nrrp}.h5", "a") as h5_file:
        h5_file.attrs.create("clamp", clamp)
        pair_group = h5_file.create_group(
            f"{input_params.pre_population}-{input_params.pre_id}"
            f"_{input_params.post_population}-{input_params.post_id}",
        )
        pair_group.attrs.create("base_seed", input_params.seed)

        # Run sweeps
        start_time = time.perf_counter()
        L.debug("### DEBUG MODE ###")
        time_current_voltage = run_sim_handler(
            simulation, input_params, nrrp, protocol, seeds, clamp, n_jobs=n_jobs
        )
        for _seed, (time_, current, voltage) in zip(seeds, time_current_voltage):
            seed_group = pair_group.create_group(f"seed{_seed}")
            seed_group.create_dataset(
                "time", data=time_, chunks=True, compression="gzip", compression_opts=9
            )
            seed_group.create_dataset(
                "soma_voltage", data=voltage, chunks=True, compression="gzip", compression_opts=9
            )
            seed_group.create_dataset(
                "soma_current",
                data=ensure_list(current),
                chunks=True,
                compression="gzip",
                compression_opts=9,
            )
        L.info("Elapsed time: %.2f", (time.perf_counter() - start_time))

    L.info("All done")
