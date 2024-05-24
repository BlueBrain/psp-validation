Tutorial
========

`psp` command (available after installing ``psp-validation``) is the main interface for running pair simulations and analyzing their output.

Please refer to

.. code-block:: console

    $ psp --help

for a brief description of available subcommands and options.

.. _Run_PSP:

Running simulations
-------------------

To run pair simulations for given pathway(s):

.. code-block:: console

    $ psp run \
        -c <simulation-config> \
        -o <output-dir> -t <targets.yaml> \
        -n NUM_PAIRS \
        -r NUM_TRIALS \
        -e EDGE_POPULATION \
        --clamp <current|voltage> \
        [<pathway.yaml>...]

where

- ``simulation-config`` is `simulation config <https://sonata-extension.readthedocs.io/en/latest/sonata_simulation.html>`__ file
- ``<pathway.yaml>`` is :ref:`pathway config <pathway-config>` file
- ``<targets.yaml>`` is :ref:`target definitions <target-definitions>` file
- ``NUM_PAIRS`` is number of pairs to simulate
- ``NUM_TRIALS`` is number of simulation trials per each pair
- ``EDGE_POPULATION`` is the name of the concerned  `edge population <https://sonata-extension.readthedocs.io/en/latest/sonata_config.html#id4>`__
- ``clamp`` allows to choose between voltage and current clamp mode (default: ``current``)


For each pathway config ``X.yaml``, `psp run` command above will (try to):

- find ``NUM_PAIRS`` pathway pairs
- for each pair:
   - run ``NUM_TRIALS`` simulations with different base seed

In *current clamp* mode, it will also:

- for each pair:
   - extract PSP amplitude from "average" voltage trace (spiking trials are not taken into account)
- calculate mean / std of obtained amplitudes
- calculate conductance scaling factor, if reference data is provided
- dump mean / std of obtained amplitudes, as well as scaling factor to :ref:`summary file <summary-file>`

For more `psp run` commands and options:

.. code-block:: console

    $ psp run --help


In particular:

--dump-traces      dump voltage / current trace for each trial to ``X.traces.h5``
--dump-amplitudes  dump PSP amplitude values to ``X.amplitudes.txt``
--jobs JOBS        use `joblib <https://joblib.readthedocs.io/en/stable/>`__ to launch multiple simulation trials in parallel

| ``X.traces.h5`` is an HDF5 file with the layout described :ref:`here <trace-dump>`.
| ``X.amplitudes.txt`` is a one-column text file with PSP amplitude value for each pair (``nan`` if amplitude could not be extracted).

In *voltage clamp* mode, ``--dump-amplitudes`` is ignored.

Collecting results
------------------

To collects values from ``.summary.yaml`` file(s) and output them in a single table:

.. code-block:: console

    $ psp summary [--with-scaling] [--style jira] [<summary.yaml>...]

For instance:

.. code-block:: console

    $ psp summary <output-dir>/L6*.summary.yaml | column -t

could give an output like:

.. code-block:: console

    pathway        reference  model
    L6_IPC-L6_BC   1.56±1.6   2.56458±1.67322
    L6_IPC-L6_BPC  0.42±0.18  1.27546±1.1145
    L6_IPC-L6_IPC  1.05±0.31  1.24938±0.879331

while

.. code-block:: console

    $ psp summary <output-dir>/L6*.summary.yaml --with-scaling --style jira

would result in

.. code-block:: console

    || pathway || reference || model || scaling ||
    | L6_IPC-L6_BC | 1.56±1.6 | 2.56458±1.67322 | 0.599359 |
    | L6_IPC-L6_BPC | 0.42±0.18 | 1.27546±1.1145 | 0.325244 |
    | L6_IPC-L6_IPC | 1.05±0.31 | 1.24938±0.879331 | 0.83799 |

output which is ready for copy-paste to JIRA or Confluence.

Plotting traces
---------------

To plot voltage / current traces and their average stored at ``.traces.h5`` file(s):

.. code-block:: console

    $ psp plot -o <output-dir> [<traces.h5>...]

For instance,

.. code-block:: console

    $ psp plot -o . <traces-dir>/L6*.traces.h5

will create a separate folder for each L6* pathway with PNG image for each simulated pair:

.. image:: images/a5526-a24711.png
   :width: 80%
