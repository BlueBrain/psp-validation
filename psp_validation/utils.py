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
    config = load_yaml(filepath)
    assert 'hold_I' not in config['protocol'], ("`hold_I` parameter in protocol is deprecated. "
                                                "Please remove it from '%s' pathway config",
                                                filepath)

    assert 'v_clamp' not in config['protocol'], (
        "`v_clamp` parameter in protocol is now deprecated. "
        "Please remove it from '%s' pathway config.\n"
        "For emulating voltage clamp, pass `--clamp voltage` to `psp run`.",
        filepath
    )

    return title, config
