"""Utility functions common to cv-validation scripts."""

import numpy as np
import pandas as pd

PAIRS_FILENAME = "pairs.csv"


def write_simulation_pairs(simulation_dir, pairs, seeds, synapse_type):
    """Saves the pairs (and seeds) selected for the simulation."""
    pre_populations, pre_ids, post_populations, post_ids = list(
        zip(*[(pre.population, pre.id, post.population, post.id) for pre, post in pairs]),
    )

    pairs_df = pd.DataFrame(
        {
            "pre_population": pre_populations,
            "pre_id": pre_ids,
            "post_population": post_populations,
            "post_id": post_ids,
            "seed": seeds,
            "synapse_type": np.full_like(seeds, synapse_type, dtype=object),
        },
    )

    simulation_dir.mkdir(exist_ok=True)
    pairs_df.to_csv(simulation_dir / PAIRS_FILENAME, index=False)


def read_simulation_pairs(simulation_dir):
    """Reads the saved pairs (and seeds) selected for the simulation."""
    return pd.read_csv(simulation_dir / PAIRS_FILENAME)


def get_pathway_outdir(pathways, outdir):
    """Get the output directory for the pathway"""
    return outdir / f"{pathways['pathway']['pre']}-{pathways['pathway']['post']}".replace(" ", "")
