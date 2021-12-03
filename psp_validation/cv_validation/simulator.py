"""
Single cell sim in BGLibPy for NRRP calibaration
author: Giuseppe Chindemi (03.2020)
+ minor modifications by András Ecker for BGLibPy compatibility (02.2021)
"""

from functools import partial
import os
import logging
import multiprocessing
import time

import h5py
import numpy as np
from bluepy_configfile.configfile import BlueConfig

LOGGER = logging.getLogger(__name__)
HSYNAPSE_ATTRIBUTES = {'Use', 'Dep', 'Fac', 'Nrrp', 'NMDA_ratio'}


def _get_hsynapse_attributes(synapses):
    """Gets the hsynapse attributes for the synapses"""
    attributes = {}

    for attr in HSYNAPSE_ATTRIBUTES:
        values = []
        for syn in synapses:
            if not hasattr(syn.hsynapse, attr):
                break
            values.append(getattr(syn.hsynapse, attr))
        else:
            attributes[attr] = values

    return attributes


def run_sim(seed, out_dir, pre_gid, post_gid, nrrp, t_stim):
    """Runs sim in BGLibPY (configs are read from user.target, out.dat and BlueConfig)"""
    # TODO: Fix "too-many-locals" in the next iteration
    # pylint: disable=too-many-locals
    import bglibpy  # pylint: disable=import-outside-toplevel

    # Apply debug to bglibpy if more verbose than INFO
    if LOGGER.getEffectiveLevel() < logging.INFO:
        bglibpy.set_verbose(100)

    with open(os.path.join(out_dir, "BlueConfig"), "r", encoding="utf-8") as fd:
        bc = BlueConfig(fd)

    bc.add_section("Connection", "NrrpOverride",
                   {"Source": "Mosaic",
                    "Destination": "Mosaic",
                    "SynapseConfigure": f"%s.Nrrp = {nrrp}"})

    ssim = bglibpy.SSim(bc, base_seed=seed)
    LOGGER.info("Seed = %i", seed)
    ssim.instantiate_gids([post_gid], synapse_detail=1, add_replay=False,
                          add_synapses=True, intersect_pre_gids=[pre_gid],
                          pre_spike_trains={pre_gid: [t_stim]})
    cell = ssim.cells[post_gid]

    for attr, values in _get_hsynapse_attributes(cell.synapses.values()).items():
        LOGGER.debug("%s = %s", attr, ", ".join(map(str, values)))

    ssim.run()
    # Get reports
    t = np.array(ssim.get_time())
    soma = np.array(ssim.get_voltage_traces()[post_gid])
    # Remove forwardskip samples
    lastfs = np.max(np.argwhere(t < 0))
    t = t[lastfs + 1:]
    soma = soma[lastfs + 1:]
    return t, soma


def run_sim_handler(out_dir, pre_gid, post_gid, nrrp, t_stim, seeds,
                    jobs=36, chunksize=1):
    """apply func to all items in it, using a process pool"""
    func = partial(run_sim,
                   out_dir=out_dir,
                   pre_gid=pre_gid,
                   post_gid=post_gid,
                   nrrp=nrrp,
                   t_stim=t_stim)
    with multiprocessing.Pool(jobs, maxtasksperchild=1) as pool:
        return pool.map(func, seeds, chunksize)


def run_simulation(seed, num_trials, pre_gid, post_gid, nrrp, t_stim, out_dir):
    """Run the simulation with the provided arguments.

    :seed: seed for random generator
    :num_trials: number of repetitions per pair
    :pre_gid: afferent neuron ID
    :post_gid: efferent neuron ID
    :nrrp: nrrp value to simulate
    """
    # TODO: Fix "too-many-locals" in the next iteration
    # pylint: disable=too-many-locals
    LOGGER.info("Starting simulation")

    # Set base seed
    np.random.seed(seed)

    # Get runtime seeds
    seeds = np.random.randint(1, 99999999 + 1, size=num_trials)

    # Create results HDF5 database
    with h5py.File(os.path.join(out_dir, f"simulation_nrrp{nrrp}.h5"), "a") as h5_file:
        pair_group = h5_file.create_group(f"{pre_gid}_{post_gid}")
        pair_group.attrs.create("base_seed", seed)

        # Run sweeps
        start_time = time.perf_counter()
        LOGGER.debug("### DEBUG MODE ###")
        time_soma = run_sim_handler(out_dir, pre_gid, post_gid, nrrp, t_stim, seeds)
        for _seed, (time_, soma) in zip(seeds, time_soma):
            seed_group = pair_group.create_group(f"seed{_seed}")
            seed_group.create_dataset("time", data=time_, chunks=True,
                                      compression="gzip", compression_opts=9)
            seed_group.create_dataset("soma", data=soma, chunks=True,
                                      compression="gzip", compression_opts=9)
        LOGGER.info("Elapsed time: %.2f", (time.perf_counter() - start_time))

    LOGGER.info("All done")
