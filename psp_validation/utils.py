"""The famous utils module."""

import multiprocessing
import pathlib
from collections.abc import Iterable

import click
import yaml

CLICK_DIR = click.Path(file_okay=False, path_type=pathlib.Path, resolve_path=True, writable=True)
CLICK_FILE = click.Path(exists=True, dir_okay=False, path_type=pathlib.Path, resolve_path=True)


def load_yaml(filepath):
    """Load YAML file."""
    return yaml.safe_load(filepath.read_text())


def load_config(filepath):
    """Load YAML job config."""
    config = load_yaml(filepath)
    assert "hold_I" not in config["protocol"], (
        "`hold_I` parameter in protocol is deprecated. "
        "Please remove it from '%s' pathway config",
        filepath,
    )

    assert "v_clamp" not in config["protocol"], (
        "`v_clamp` parameter in protocol is now deprecated. "
        "Please remove it from '%s' pathway config.\n"
        "For emulating voltage clamp, pass `--clamp voltage` to `psp run`.",
        filepath,
    )
    return config


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
    return list(v) if isinstance(v, Iterable) and not isinstance(v, str) else [v]
