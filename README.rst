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
the transition. To achieve identical results two adjustments are neccesary:

* Seeds for individual simulations are based on node ids, edge ids and population names. 
  These seeds need to be fixed to a constant value. In psp-validations and in BlueCelluLab.

* Pair selection is not identical. Pairs returned in `pathways.py` need to be set to return
  the same list of id pairs.

With these two adjustments the results of BlueConfig and Sonata are identical.

Sufficient number of repetitions (`-r`) diminishes the influence of seeds and so even
without fixing the seed to a constant value the results are remarkably close.

Using ``300`` repetitions and fixing the id pairs, these are the summary values:

* Sonata

    .. code:: 

        mean: 0.5758531759392852
        std: 0.5048845104283485

* BlueConfig

    .. code:: 

        mean: 0.5760417780829513
        std: 0.4978064245906366

Finally these are the summary values for ``1000`` repetitions and with no adjustments to the code (the cell pairs are possibly different):

* Sonata

    .. code:: 

        mean: 0.6876990851736935
        std: 0.43105991059029075

* BlueConfig

    .. code:: 

        mean: 0.571458741985596
        std: 0.48709744084273227

CV-validations transition has been verified in a similar fassion. 
