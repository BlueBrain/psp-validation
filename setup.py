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
        'pandas>=1.3,<2',
        'tqdm>=4.0',
        'neuron>=7.8.0',
        'bglibpy>=4.11.1,<5',
        'bluepy>=2.1,<3.0',
        'seaborn>=0.11,<1.0',
    ],
    extras_require={"docs": ["sphinx", "sphinx-bluebrain-theme"]},
    packages=find_packages(),
    author="BlueBrain NSE",
    author_email="bbp-ou-nse@groupes.epfl.ch",
    description="PSP analysis tools",
    long_description="PSP analysis tools",
    long_description_content_type="text/plain",
    license="BBP-internal-confidential",
    python_requires='>=3.7',
    entry_points={
        'console_scripts': ['psp=psp_validation.cli:cli',
                            'cv-validation=psp_validation.cv_validation.cli:cli']},
    url="https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
    download_url="git@bbpgitlab.epfl.ch:nse/psp-validation.git",
    project_urls={
        "Tracker": "https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
        "Source": "https://bbpgitlab.epfl.ch/nse/psp-validation",
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
