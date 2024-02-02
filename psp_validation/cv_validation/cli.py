"""
CV validation analysis toolkit.

 * `cv-validation setup`
"""

import os
import logging

import click
import numpy as np

from psp_validation import setup_logging
from psp_validation.utils import load_config, load_yaml
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
@click.option("-c", "--simulation-config", required=True, help="Path to SONATA simulation config")
@click.option("-o", "--output-dir", required=True, help="Path to output folder")
@click.option("-p", "--pathways", required=True, help="Path to pathway definitions")
@click.option("-t", "--targets", required=True, help="Path to target definitions")
@click.option("-n", "--num-pairs", type=int, required=True,
              help="Sample NUM_PAIRS pairs from each pathway"
              )
@click.option("--seed", type=int, required=False, default=None,
              help="Seed used to initialize the Numpy random number generator.")
def setup(simulation_config, output_dir, pathways, targets, num_pairs, seed):
    """Set up the simulation and pairs to simulate."""
    if seed is not None:
        np.random.seed(seed)
    setup_simulation(simulation_config,
                     output_dir,
                     load_config(pathways),
                     load_yaml(targets),
                     num_pairs)


@cli.command()
@click.option("-o", "--output-dir", required=True, help="Path to output folder")
@click.option("-p", "--pathways", required=True, help="Path to pathway definitions")
@click.option("-r", "--num-trials", type=int, required=True,
              help="Run NUM_TRIALS simulations for each pair")
@click.option("--nrrp", nargs=2, type=int, required=True, help="NRRP range given as: <min> <max>")
@click.option(
    "-m", "--clamp", type=click.Choice(['current', 'voltage']),
    help="Clamp type used", default='current', show_default=True
)
@click.option(
    "-j", "--jobs", type=int,
    help=(
        "Number of trials to run in parallel"
        "(if not specified, trials are run sequentially; "
        "setting to 0 would use all available CPUs)"
    )
)
def run(output_dir, pathways, num_trials, nrrp, clamp, jobs):
    """Run the simulation with the data configured in setup."""
    simulation_dir = os.path.join(output_dir, 'simulations')
    pre_post_seeds = read_simulation_pairs(simulation_dir)
    config = load_config(pathways)

    for nrrp_ in range(nrrp[0], nrrp[1] + 1):
        for row in pre_post_seeds.itertuples():
            run_simulation(row, num_trials, nrrp_, config['protocol'], simulation_dir, clamp, jobs)


@cli.command()
@click.option("-o", "--output-dir", required=True, help="Path to output folder")
@click.option("-p", "--pathways", required=True, help="Path to pathway definitions")
@click.option("--nrrp", nargs=2, type=int, required=True, help="NRRP range given as: <min> <max>")
@click.option("-n", "--num-pairs", type=int, default=None,
              help="Number of pairs to randomly choose from the simulation")
@click.option("-r", "--num-reps", type=int, default=None,
              help="Number iterations (repetitions) done for each lambda value")
@click.option(
    "-j", "--jobs", type=int,
    help=(
        "Number of trials to run in parallel"
        "(if not specified, trials are run sequentially; "
        "setting to 0 would use all available CPUs)"
    )
)
def calibrate(output_dir, pathways, nrrp, num_pairs, num_reps, jobs):
    """Analyse the simulation results."""
    config = load_config(pathways)
    pathway_name = (
        f"{config['pathway']['pre']}_{config['pathway']['post']}"
    ).replace(" ", "")
    run_calibration(output_dir, config, pathway_name, nrrp,
                    n_pairs=num_pairs, n_reps=num_reps, n_jobs=jobs)
