psp-validation
================

Validation of Post Synaptic Potentials (PSPs)


Installation
------------

.. code:: bash

    $ pip install psp-validation

Usage
-----

Cli
^^^
The recommended usage is via the command line interface.
To run simulations of psp with the test data:

.. code:: bash

    psp run
        -c tests/input_data/simple/simulation_config.json \
        -t tests/input_data/simple/usecases/hippocampus/targets.yaml \
        -e default \
        tests/input_data/pathway.yaml \
        -o out \
        -n 1 \
        -r 1 \
        -j 1 \
        --dump-traces \
        --dump-amplitudes \
        --seed 400

``-vv`` options stands for verbosity of log output.
There are 3 different values for it:

- ``-v`` is for showing only warnings and errors
- ``-vv`` additionally to ``-v`` shows info messages
- ``-vvv`` additionally shows debug messages.

By default ``-v`` is used.

Somatosensory cortex (SSCx) example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After downloading the circuit model from `Zenodo <https://zenodo.org/records/8155899>`_ and creating `out` for simulation outputs

edit `usecases/sscx/simulation_config.json` and run:

.. code:: bash

    psp -vv run
        -c usecases/sscx/simulation_config.json
        -t usecases/sscx/targets_v6.yaml
        -e S1nonbarrel_neurons__S1nonbarrel_neurons__chemical
        -o out/
        -n 50
        -r 35
        -j 35 usecases/sscx/pathways/primary/L5_TTPC-L5_TTPC.yaml.yaml
        --dump-traces
        --dump-amplitudes

which will sample 50 pairs of connected L5 thick thufted pyramidal cells from the circuit, trigger a single presynaptic spike from the presynaptic ones

and record the PSP on the postsynaptic ones. The process will be repeated 35 times (as synapses are stochastic and thus PSP varry in amplitude)

on 35 CPUs in parallel. It will saved the postsynaptic traces (to `.h5`), mean PSP amplitudes (to `.txt`) and a summary with a calculated conductance (g_syn)

scaling factor (to `.yaml`).

Testing
^^^^^^^

.. code:: bash

    tox -e py310


Citation
--------

If you use this software, kindly use the following BibTeX entry for citation:

.. code:: bash

    @article{Ecker2020,
    author = {Ecker, Andr{\'{a}}s and Romani, Armando and S{\'{a}}ray, S{\'{a}}ra and K{\'{a}}li, Szabolcs and Migliore, Michele and Falck, Joanne and Lange, Sigrun and Mercer, Audrey and Thomson, Alex M. and Muller, Eilif and Reimann, Michael W. and Ramaswamy, Srikanth},
    doi = {10.1002/hipo.23220},
    journal = {Hippocampus},
    number = {11},
    pages = {1129--1145},
    pmid = {32520422},
    title = {{Data-driven integration of hippocampal CA1 synaptic physiology in silico}},
    volume = {30},
    year = {2020}
    }


Acknowledgements
================

The development of this software was supported by funding to the Blue Brain Project, a research center of the École polytechnique fédérale de Lausanne (EPFL), from the Swiss government’s ETH Board of the Swiss Federal Institutes of Technology.

This project/research received funding from the European Union’s Horizon 2020 Framework Programme for Research and Innovation under the Framework Partnership Agreement No. 650003 (HBP FPA).

For license and authors, see LICENSE.txt and AUTHORS.txt respectively.

Copyright (c) 2022-2024 Blue Brain Project/EPFL
