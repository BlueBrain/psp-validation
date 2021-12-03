"""
Sets up NRRP simulations in BGLibPy
by András Ecker based on Giuseppe Chindemi's code
last modified: 02.2021
"""

import logging
import os
from functools import partial

import numpy as np

from bluepy import Circuit
from bluepy.enums import Cell
from bluepy.utils import take_n

from psp_validation.features import get_synapse_type
from psp_validation.cv_validation.utils import (ensure_dir_exists,
                                                read_blueconfig_template,
                                                write_simulation_pairs)

LOGGER = logging.getLogger(__name__)


def is_valid_connection(connection, circuit, constraints):
    """Checks connection against distance constraints"""
    # TODO: this can be removed in the next iteration (use psp_validation.pathways.get_pairs)
    coord = circuit.cells.get(connection, [Cell.X, Cell.Y, Cell.Z]).to_numpy()
    dist = np.abs(np.diff(coord, axis=0))
    return np.all(dist < constraints)


def get_pairs(circuit, pathway, targets, n_pairs):
    """Samples pairs from the circuit"""
    # TODO: this can be removed in the next iteration (use psp_validation.pathways.get_pairs)?
    pre_query = targets[pathway['pre']]
    post_query = targets[pathway['post']]
    constraints = np.array([pathway['constraints']['max_dist_x'],
                            pathway['constraints']['max_dist_y'],
                            pathway['constraints']['max_dist_z']])
    # Unique gids is needed here as one biasing postsynaptic neuron can spoil the results
    connections = circuit.connectome.iter_connections(pre_query, post_query, unique_gids=True)
    filter_func = partial(is_valid_connection, circuit=circuit, constraints=constraints)
    return take_n(filter(filter_func, connections), n_pairs)


def write_blue_config(output_dir, circuit, circuit_path, target, protocol):
    """Creates the BlueConfig file from the template"""
    LOGGER.info('Writing BlueConfig from a template...')
    simulation_dir = os.path.join(output_dir, 'simulations')
    ensure_dir_exists(simulation_dir)
    write_path = os.path.join(simulation_dir, "BlueConfig")

    if os.path.exists(write_path):
        LOGGER.warning("Path %s already exists. Will not overwrite.", write_path)
        return

    bc_template = read_blueconfig_template()

    with open(write_path, "w") as f:
        f.write(bc_template.format(
            circuit_path=circuit_path,
            nrn_path=circuit.config["connectome"],
            morphology_path=circuit.config["morphologies"],
            metype_path=circuit.config["emodels"],
            mecombo_file=circuit.config["mecombo_info"],
            target=target,
            duration=protocol['t_stim'] + 200))


def write_pairs_and_seeds(pathway, targets, circuit, n_pairs, output_dir):
    """Gets desired number of pairs and seeds for the pathway and saves them to a file."""
    LOGGER.info('Setting pairs and seeds for simulation...')
    pairs = get_pairs(circuit, pathway, targets, n_pairs)

    # Arbitrary random value range for seeds
    seeds = np.random.randint(1, 99999999 + 1, len(pairs))
    syn_type = get_synapse_type(circuit,
                                [pre for (pre, _) in pairs])
    write_simulation_pairs(os.path.join(output_dir, 'simulations'), pairs, seeds, syn_type)


def setup_simulation(circuit_config, output_dir, pathway, targets, num_pairs, target_region):
    """Entry point for setting up the simulation directory, pairs etc."""
    LOGGER.info("Setting up directories and files for simulation...")
    circuit = Circuit(circuit_config)
    circuit_dir = os.path.dirname(circuit_config)
    write_blue_config(output_dir, circuit, circuit_dir, target_region, pathway['protocol'])
    write_pairs_and_seeds(pathway['pathway'], targets, circuit, num_pairs, output_dir)
    LOGGER.info("Done")
