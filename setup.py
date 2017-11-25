#!/usr/bin/env python
# pylint: disable=missing-docstring

from setuptools import setup

from psp_validation.version import __version__


setup(
    name="psp_validation",
    version=__version__,
    install_requires=[
        'click>=6.0',
        'tqdm>=4.0',
        'numpy>=1.10',
        'h5py>=2.7',
        'bglibpy>=3.2.14,<4.0',
        'bluepy>=0.11.10,<0.12',
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
        'apps/psp',
    ],
    url="https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
    download_url="ssh://bbpcode.epfl.ch/nse/psp-validation",
    include_package_data=True
)
