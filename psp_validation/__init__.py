""" PSP analysis tools. """
import logging

from psp_validation.version import __version__


LOGGER = logging.getLogger(__name__)


def setup_logging(level):
    """ Setup application logger. """
    logging.basicConfig(level=logging.WARNING)
    LOGGER.setLevel(level=level)


class PSPError(Exception):
    """ Base `psp_validation` exception """
