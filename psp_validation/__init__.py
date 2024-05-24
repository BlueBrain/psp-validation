"""PSP analysis tools."""

import logging

L = logging.getLogger(__name__)


def setup_logging(level):
    """Setup application logger."""
    logformat = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    logging.basicConfig(level=logging.WARNING, format=logformat)
    L.setLevel(level=level)


class PSPError(Exception):
    """Base `psp_validation` exception"""
