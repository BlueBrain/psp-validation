import os
import yaml


def load_config(filepath):
    """ Load YAML job config. """
    title = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, 'r') as f:
        config = yaml.load(f)
    return title, config
