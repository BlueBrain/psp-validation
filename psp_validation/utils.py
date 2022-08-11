"""The famous utils module."""
from collections.abc import Iterable
import multiprocessing
import os

import yaml


def load_yaml(filepath):
    """Load YAML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def load_config(filepath):
    """Load YAML job config."""
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


def isolate(func):
    """Isolate a function in a separate process.

    Note: it does not work as a decorator.
    Note: initially based on morph-tool, removing NestedPool because incompatible with Python 3.8.

    Args:
        func (function): function to isolate.

    Returns:
        the isolated function
    """
    def func_isolated(*args, **kwargs):
        with multiprocessing.Pool(1, maxtasksperchild=1) as pool:
            return pool.apply(func, args, kwargs)

    return func_isolated


def ensure_list(v):
    """Convert iterable / wrap scalar/str into list."""
    if isinstance(v, Iterable) and not isinstance(v, str):
        return list(v)
    else:
        return [v]
