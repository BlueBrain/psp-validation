'''The famous utils module'''
import os
import yaml


def load_yaml(filepath):
    """ Load YAML file. """
    with open(filepath, 'r') as f:
        return yaml.load(f)


def load_config(filepath):
    """ Load YAML job config. """
    title = os.path.splitext(os.path.basename(filepath))[0]
    return title, load_yaml(filepath)
