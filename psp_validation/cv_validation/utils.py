"""Utility functions common to cv-validation scripts."""
import os
from importlib_resources import files

import numpy as np
import pandas as pd

from psp_validation.cv_validation import templates


SONATA_TEMPLATE_FILENAME = 'sonata.json.tmpl'
PAIRS_FILENAME = 'pairs.csv'


def ensure_dir_exists(dirpath):
    """Creates a directory if it doesn't already exist."""
    os.makedirs(dirpath, exist_ok=True)


def read_sonata_template():
    """Reads and returns the contents of the Sonata template file."""
    return files(templates).joinpath(SONATA_TEMPLATE_FILENAME).read_text(encoding="utf-8")


def write_simulation_pairs(simulation_dir, pairs, seeds, synapse_type):
    """Saves the pairs (and seeds) selected for the simulation."""
    pre_populations, pre_ids, post_populations, post_ids = list(
        zip(*[(pre.population, pre.id, post.population, post.id) for pre, post in pairs]))

    df = pd.DataFrame({'pre_population': pre_populations,
                       'pre_id': pre_ids,
                       'post_population': post_populations,
                       'post_id': post_ids,
                       'seed': seeds,
                       'synapse_type': np.full_like(seeds, synapse_type, dtype=object)})

    df.to_csv(os.path.join(simulation_dir, PAIRS_FILENAME), index=False)


def read_simulation_pairs(simulation_dir):
    """Reads the saved pairs (and seeds) selected for the simulation."""
    return pd.read_csv(os.path.join(simulation_dir, PAIRS_FILENAME))
