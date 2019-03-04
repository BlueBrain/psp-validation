#!/usr/bin/env python
# pylint: disable=missing-docstring

from setuptools import setup, find_packages

from psp_validation.version import __version__


setup(
    name="psp-validation",
    version=__version__,
    install_requires=[
        'click>=7.0',
        'future>=0.16',
        'h5py>=2.7',
        'numpy>=1.10',
        'tqdm>=4.0',
    ] + [
        'bglibpy>=3.2.47,<4.0',
        'bluepy>=0.13',
    ],
    packages=find_packages(),
    author="BlueBrain NSE",
    author_email="bbp-ou-nse@groupes.epfl.ch",
    description="PSP analysis tools",
    license="BBP-internal-confidential",
    scripts=[
        'apps/psp',
    ],
    url="https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
    download_url="ssh://bbpcode.epfl.ch/nse/psp-validation",
    include_package_data=True
)
