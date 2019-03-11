""" PSP analysis tools. """
import logging

from psp_validation.version import __version__


_LOGGER = logging.getLogger('psp')


def setup_logging(level):
    """ Setup application logger. """
    logging.basicConfig(level=logging.WARNING)
    _LOGGER.setLevel(level=level)


def get_logger(name=None):
    """ Get / create 'psp' logger. """
    if name is None:
        return _LOGGER
    else:
        return _LOGGER.getChild(name)


class PSPError(Exception):
    """ Base `psp_validation` exception """
