psp-validation
================

Validation of post synaptic potential.


Installation
------------

The project is available as a module.

.. code:: bash

    module load unstable neurodamus-hippocampus psp-validation

Usage
-----
It is recommended to run the project only on BB5.

Cli
^^^
The recommended usage is via the command line interface API. To run simulations of psp with
the test data:

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

`-vv` options stands for verbosity of log output. There are 3 different values for it: `-v`, `-vv`,
`-vvv`. `-v` is for showing only warnings and errors. `-vv` additionally to `-v` shows info
messages. `-vvv` additionally shows debug messages. By default `-v` is used. This flag is common to
all NSE projects, and is usually used right after the main command and before the supplementary
command. The main command is `psp`, the supplementary command is `run`.

Testing
^^^^^^^
It is highly suggested to use BB5 for running tests manually.

.. code:: bash

    tox -e py310

Transition from BlueConfig to Sonata
------------------------------------

Simulations using BlueConfig and Sonata describing the same circuit have been run to validate
the transition.

``psp-validation`` using ``BlueConfig`` + ``bglibpy`` returns the same exact results as when using ``SONATA`` + ``bluecellulab``.
However, there are a few caveats:

* internal seeds of bluecellulab/bglibpy need to be manually fixed to same numbers

* same edges (pre-post pairs) need to be selected

* ``bluecellulab`` needs to be tweaked to use ``afferent_section_pos`` from a ``h5`` file

  * fix for this is pending (see: https://github.com/BlueBrain/BlueCelluLab/pull/168)

* if ``libsonata<0.1.25`` is used with SONATA configs, make sure ``celsius=34`` is passed to ``SSim.run``/``CircuitSimulation.run`` functions of ``bglibpy``/``bluecellulab``

CV-validations transition has been verified in a similar fashion.
