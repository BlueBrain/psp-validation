"""
CV validation analysis toolkit.

 * `cv-validation setup`
"""

import logging

import click
import numpy as np

from psp_validation import setup_logging
from psp_validation.utils import load_config, load_yaml
from psp_validation.version import VERSION
from psp_validation.cv_validation.calibrate_NRRP import run_calibration
from psp_validation.cv_validation.setsim import setup_simulation
from psp_validation.cv_validation.simulator import run_simulation
from psp_validation.cv_validation.utils import read_simulation_pairs, get_pathway_outdir


def _parse_pathways_and_output_dir(pathways, outdir):
    pathways = load_config(pathways)
    return pathways, get_pathway_outdir(pathways, outdir)


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
@click.option("-e", "--edge-population", type=str, required=True,
              help="Edge population for the pathway")
@click.option("-n", "--num-pairs", type=int, required=True,
              help="Sample NUM_PAIRS pairs from each pathway")
@click.option("--seed", type=int, required=False, default=None,
              help="Seed used to initialize the Numpy random number generator.")
def setup(simulation_config, output_dir, pathways, targets, edge_population, num_pairs, seed):
    """Set up the pairs to simulate."""
    pathways, output_dir = _parse_pathways_and_output_dir(pathways, output_dir)
    if seed is not None:
        np.random.seed(seed)

    setup_simulation(simulation_config, edge_population, output_dir,
                     pathways, load_yaml(targets), num_pairs)


@cli.command()
@click.option("-c", "--simulation-config", required=True, help="Path to SONATA simulation config")
@click.option("-o", "--output-dir", required=True, help="Path to output folder")
@click.option("-p", "--pathways", required=True, help="Path to pathway definitions")
@click.option("-r", "--num-trials", type=int, required=True,
              help="Run NUM_TRIALS simulations for each pair")
@click.option("--nrrp", nargs=2, type=int, required=True, help="NRRP range given as: <min> <max>")
@click.option("-m", "--clamp", type=click.Choice(['current', 'voltage']),
              help="Clamp type used", default='current', show_default=True)
@click.option(
    "-j", "--jobs", type=int,
    help=(
        "Number of trials to run in parallel"
        "(if not specified, trials are run sequentially; "
        "setting to 0 would use all available CPUs)"
    )
)
def run(simulation_config, output_dir, pathways, num_trials, nrrp, clamp, jobs):
    """Run the simulation with the data configured in setup."""
    pathways, output_dir = _parse_pathways_and_output_dir(pathways, output_dir)
    pre_post_seeds = read_simulation_pairs(output_dir)

    for nrrp_ in range(nrrp[0], nrrp[1] + 1):
        for row in pre_post_seeds.itertuples():
            run_simulation(
                simulation_config, row, num_trials, nrrp_,
                pathways['protocol'], output_dir, clamp, jobs,
            )


@cli.command()
@click.option("-o", "--output-dir", required=True, help="Path to output folder")
@click.option("-p", "--pathways", required=True, help="Path to pathway definitions")
@click.option("--nrrp", nargs=2, type=int, required=True, help="NRRP range given as: <min> <max>")
@click.option("-n", "--num-pairs", type=int, default=None,
              help="Number of pairs to randomly choose from the simulation")
@click.option("-r", "--num-reps", type=int, default=None,
              help="Number iterations (repetitions) done for each lambda value")
@click.option("-j", "--jobs", type=int,
              help=("Number of trials to run in parallel"
                    "(if not specified, trials are run sequentially; "
                    "setting to 0 would use all available CPUs)"))
def calibrate(output_dir, pathways, nrrp, num_pairs, num_reps, jobs):
    """Analyse the simulation results."""
    pathways, output_dir = _parse_pathways_and_output_dir(pathways, output_dir)
    run_calibration(output_dir, pathways, nrrp, n_pairs=num_pairs, n_reps=num_reps, n_jobs=jobs)
