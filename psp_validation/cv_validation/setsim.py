"""
Sets up NRRP simulations in bluecellulab
by András Ecker based on Giuseppe Chindemi's code
last modified: 02.2021
"""

import logging
import os

import numpy as np

from bluepysnap import Simulation

from psp_validation.features import get_synapse_type
from psp_validation.pathways import get_pairs
from psp_validation.cv_validation.utils import (ensure_dir_exists,
                                                read_sonata_template,
                                                write_simulation_pairs)

L = logging.getLogger(__name__)


def write_config(output_dir, protocol, simulation):
    """Creates the Sonata simulation config file from the template"""
    L.info('Writing Sonata simulation config from a template...')
    simulation_dir = os.path.join(output_dir, 'simulations')
    ensure_dir_exists(simulation_dir)
    write_path = os.path.join(simulation_dir, "sonata_config.json")

    if os.path.exists(write_path):
        L.warning("Path %s already exists. Will not overwrite.", write_path)
        return

    sonata_config = read_sonata_template().format(
        network=simulation.to_libsonata.network,
        node_sets_file=simulation.to_libsonata.node_sets_file,
        duration=protocol['t_stim'] + 200,
    )

    with open(write_path, "w", encoding='utf-8') as f:
        f.write(sonata_config)


def write_pairs_and_seeds(pathway, targets, circuit, n_pairs, output_dir):
    """Gets desired number of pairs and seeds for the pathway and saves them to a file."""
    L.info('Setting pairs and seeds for simulation...')

    pre = targets.get(pathway["pre"], pathway["pre"])
    post = targets.get(pathway["post"], pathway["post"])

    pairs = get_pairs(
        circuit,
        pre,
        post,
        num_pairs=n_pairs,
        population=pathway["edge_population"]
    )
    # Arbitrary random value range for seeds
    seeds = np.random.randint(1, 99999999 + 1, len(pairs))
    syn_type = get_synapse_type(
        circuit,
        circuit.nodes.ids(pathway["pre"])
    )
    write_simulation_pairs(os.path.join(output_dir, 'simulations'), pairs, seeds, syn_type)


def setup_simulation(simulation_config, output_dir, pathway, targets, num_pairs):
    """Entry point for setting up the simulation directory, pairs etc."""
    L.info("Setting up directories and files for simulation...")
    simulation = Simulation(simulation_config)
    write_config(output_dir, pathway['protocol'], simulation)
    write_pairs_and_seeds(pathway['pathway'], targets, simulation.circuit, num_pairs, output_dir)
    L.info("Done")
