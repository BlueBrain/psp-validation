#!/usr/bin/env python
# pylint: disable=missing-docstring

from setuptools import setup

from psp_validation.version import __version__


setup(
    name="psp_validation",
    version=__version__,
    install_requires=[
        'numpy>=1.10',
        'h5py>=2.7',
        'bglibpy>=3.1,<4.0',
        'bluepy>=0.11,<0.12',
        'nose>=1.3',
    ],
    packages=[
        'psp_validation',
    ],
    author="Eilif Muller, Arseny V. Povolotsky",
    author_email="arseny.povolotsky@epfl.ch",
    description="PSP analysis tools",
    license="BBP-internal-confidential",
    scripts=[
        'apps/analyse_psp_traces.py',
        'apps/make_psp_traces.py',
    ],
    url="https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
    download_url="ssh://bbpcode.epfl.ch/nse/psp-validation",
    include_package_data=True
)
