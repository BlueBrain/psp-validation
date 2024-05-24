"""
Sets up NRRP simulations in bluecellulab
by András Ecker based on Giuseppe Chindemi's code
last modified: 02.2021
"""

import logging

import numpy as np

from bluepysnap import Simulation

from psp_validation.features import get_synapse_type
from psp_validation.pathways import get_pairs
from psp_validation.cv_validation.utils import write_simulation_pairs

L = logging.getLogger(__name__)


def write_pairs_and_seeds(pathway, targets, edge_population, n_pairs, output_dir):
    """Gets desired number of pairs and seeds for the pathway and saves them to a file."""
    L.info('Setting pairs and seeds for simulation...')

    pre = targets.get(pathway["pre"], pathway["pre"])
    post = targets.get(pathway["post"], pathway["post"])

    pairs = get_pairs(edge_population, pre, post, num_pairs=n_pairs)

    # Arbitrary random value range for seeds
    seeds = np.random.randint(1, 99999999 + 1, len(pairs))
    syn_type = get_synapse_type(edge_population.source, pre)

    write_simulation_pairs(output_dir, pairs, seeds, syn_type)


def setup_simulation(simulation_config, edge_population, output_dir, pathway, targets, num_pairs):
    """Entry point for setting up the simulation directory, pairs etc."""
    L.info("Setting up directories and files for simulation...")
    edge_population = Simulation(simulation_config).circuit.edges[edge_population]
    write_pairs_and_seeds(pathway['pathway'], targets, edge_population, num_pairs, output_dir)
    L.info("Done")
