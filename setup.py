from setuptools import setup, find_packages

from psp_validation.version import __version__


setup(
    name="psp-validation",
    version=__version__,
    install_requires=[
        'click>=7.0',
        'efel>=3.0.39',
        'h5py>=2.7',
        'joblib>=0.13',
        'numpy>=1.10',
        'tqdm>=4.0',
        'neuron>=7.8.0',
    ] + [
        'bglibpy>=4.0.13,<5.0',
        'bluepy[sonata]>=0.14.3',
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
