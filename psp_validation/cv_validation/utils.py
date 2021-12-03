"""Utility functions common to cv-validation scripts."""
import os
import importlib.resources

import numpy as np
import pandas as pd

from psp_validation.cv_validation import templates

BLUECONFIG_TEMPLATE_FILENAME = 'BlueConfig.tmpl'
PAIRS_FILENAME = 'pairs.csv'


def ensure_dir_exists(dirpath):
    """Creates a directory if it doesn't already exist."""
    os.makedirs(dirpath, exist_ok=True)


def read_blueconfig_template():
    """Reads and returns the contents of the BlueConfig template file."""
    return importlib.resources.read_text(templates, BLUECONFIG_TEMPLATE_FILENAME)


def write_simulation_pairs(simulation_dir, pairs, seeds, synapse_type):
    """Saves the pairs (and seeds) selected for the simulation."""
    pre, post = np.asarray(pairs).T

    df = pd.DataFrame({'pre': pre,
                       'post': post,
                       'seed': seeds,
                       'synapse_type': np.full_like(seeds, synapse_type, dtype=object)})

    df.to_csv(os.path.join(simulation_dir, PAIRS_FILENAME), index=False)


def read_simulation_pairs(simulation_dir):
    """Reads the saved pairs (and seeds) selected for the simulation."""
    return pd.read_csv(os.path.join(simulation_dir, PAIRS_FILENAME))
