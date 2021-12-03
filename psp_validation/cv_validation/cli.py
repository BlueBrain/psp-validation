"""
PSP analysis toolkit.

 * `psp run`     Run pair simulations for given pathway(s)
 * `psp summary` Collect `psp run` summary output
 * `psp plot`    Plot voltage / current traces obtained with `psp run`
"""

import os
import logging

import click
import numpy as np

from psp_validation import setup_logging
from psp_validation.utils import load_yaml
from psp_validation.version import VERSION
from psp_validation.cv_validation.calibrate_NRRP import run_calibration
from psp_validation.cv_validation.setsim import setup_simulation
from psp_validation.cv_validation.simulator import run_simulation
from psp_validation.cv_validation.utils import read_simulation_pairs


@click.group()
@click.version_option(version=VERSION)
@click.option("-v", "--verbose", count=True, help="-v for INFO, -vv for DEBUG")
def cli(verbose=0):
    """ CV analysis tool """
    level = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG
    }[verbose]
    setup_logging(level)


@cli.command()
@click.option("-c", "--circuit-config", required=True, help="Path to circuit config")
@click.option("-o", "--output-dir", required=True, help="Path to output folder")
@click.option("-p", "--pathways", required=True, help="Path to pathway definitions")
@click.option("-t", "--targets", required=True, help="Path to target definitions")
@click.option("-n", "--num-pairs", type=int, required=True,
              help="Sample NUM_PAIRS pairs from each pathway"
              )
@click.option("--seed", type=int, required=False, default=None,
              help="Seed used to initialize the Numpy random number generator.")
def setup(circuit_config, output_dir, pathways, targets, num_pairs, seed):
    """Set up the simulation with BlueConfig and pairs to simulate."""
    if seed is not None:
        np.random.seed(seed)
    setup_simulation(circuit_config,
                     output_dir,
                     load_yaml(pathways),
                     load_yaml(targets),
                     num_pairs,
                     'S1HL')


@cli.command()
@click.option("-o", "--output-dir", required=True, help="Path to output folder")
@click.option("-p", "--pathways", required=True, help="Path to pathway definitions")
@click.option("-r", "--num-trials", type=int, required=True,
              help="Run NUM_TRIALS simulations for each pair")
@click.option("--nrrp", nargs=2, type=int, required=True, help="NRRP range given as: <min> <max>")
def run(output_dir, pathways, num_trials, nrrp):
    """Run the simulation with the data configured in setup."""
    simulation_dir = os.path.join(output_dir, 'simulations')
    pre_post_seeds = read_simulation_pairs(simulation_dir)
    pathway = load_yaml(pathways)
    t_stim = pathway['protocol']['t_stim']

    for nrrp_ in range(nrrp[0], nrrp[1] + 1):
        for row in pre_post_seeds.itertuples():
            run_simulation(row.seed, num_trials, row.pre, row.post, nrrp_, t_stim, simulation_dir)


@cli.command()
@click.option("-o", "--output-dir", required=True, help="Path to output folder")
@click.option("-p", "--pathways", required=True, help="Path to pathway definitions")
@click.option("--nrrp", nargs=2, type=int, required=True, help="NRRP range given as: <min> <max>")
@click.option("-n", "--num-pairs", type=int, default=None,
              help="Number of pairs to randomly choose from the simulation")
@click.option("-r", "--num-reps", type=int, default=None,
              help="Number iterations (repetitions) done for each lambda value")
def calibrate(output_dir, pathways, nrrp, num_pairs, num_reps):
    """Analyse the simulation results."""
    pathway = load_yaml(pathways)
    pathway_name = f"{pathway['pathway']['pre']}-{pathway['pathway']['post']}"
    run_calibration(output_dir, pathway, pathway_name, nrrp,
                    n_pairs=num_pairs, n_reps=num_reps)
