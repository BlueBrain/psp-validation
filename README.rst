psp-validation
================

Validation of post synaptic potential.


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
* ``-v`` is for showing only warnings and errors
* ``-vv`` additionally to ``-v`` shows info messages
* ``-vvv`` additionally shows debug messages.

By default ``-v`` is used.

Testing
^^^^^^^

.. code:: bash

    tox -e py310

Acknowledgements
================

The development of this software was supported by funding to the Blue Brain Project, a research center of the École polytechnique fédérale de Lausanne (EPFL), from the Swiss government’s ETH Board of the Swiss Federal Institutes of Technology.

For license and authors, see LICENSE.txt and AUTHORS.txt respectively.

Copyright (c) 2022-2024 Blue Brain Project/EPFL
