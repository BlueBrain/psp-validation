"""setup"""
from setuptools import find_packages, setup

setup(
    name="psp-validation",
    install_requires=[
        "attrs>=20.3.0",
        "click>=7.0",
        "efel>=3.0.39",
        "h5py>=3,<4",
        "joblib>=0.16",
        "matplotlib",
        "numpy>=1.10",
        "pandas>=1.3,<2",
        "tqdm>=4.0",
        "bluecellulab>=2.6.15",
        "bluepysnap>=3.0.0,<4.0.0",
        "seaborn>=0.11,<1.0",
    ],
    extras_require={"docs": ["sphinx", "sphinx-bluebrain-theme"]},
    packages=find_packages(),
    author="BlueBrain NSE",
    author_email="bbp-ou-nse@groupes.epfl.ch",
    description="PSP analysis tools",
    long_description="PSP analysis tools",
    long_description_content_type="text/plain",
    license="Apache2.0",
    python_requires=">=3.7",
    setup_requires=[
        "setuptools_scm",
    ],
    use_scm_version={
        "write_to": "psp_validation/version.py",
    },
    entry_points={
        "console_scripts": ["psp=psp_validation.cli:cli",
                            "cv-validation=psp_validation.cv_validation.cli:cli"]},
    url="https://github.com/BlueBrain/psp-validation/",
    project_urls={
        "Tracker": "https://github.com/BlueBrain/psp-validation/issues",
        "Source": "https://github.com/BlueBrain/psp-validation/",
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
