from setuptools import setup, find_packages

from psp_validation.version import __version__


setup(
    name="psp-validation",
    version=__version__,
    install_requires=[
        'attrs>=20.3.0',
        'click>=7.0',
        'efel>=3.0.39',
        'h5py>=3,<4',
        'joblib>=0.16',
        'numpy>=1.10',
        'tqdm>=4.0',
        'neuron>=7.8.0',
        'bglibpy>=4.4.27,<5.0',
        'bluepy>=2.1,<3.0',
    ],
    packages=find_packages(),
    author="BlueBrain NSE",
    author_email="bbp-ou-nse@groupes.epfl.ch",
    description="PSP analysis tools",
    license="BBP-internal-confidential",
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['psp=psp_validation.cli:cli']},
    url="https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
    download_url="ssh://bbpcode.epfl.ch/nse/psp-validation",
    include_package_data=True
)
