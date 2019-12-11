Installation
============

module load
-----------

The easiest way to get ``psp-validation`` package might be with a *module*:

.. code-block:: console

    $ module purge
    $ module load neuron
    $ module load neurodamus-core  # to set BGLIBPY_MOD_LIBRARY_PATH
    $ module load psp-validation

For hippocampus:

.. code-block:: console

    $ module purge
    $ module load neuron
    $ module load neurodamus-hippocampus
    $ export BGLIBPY_MOD_LIBRARY_PATH=$BBP_HOME/lib/libnrnmech.so
    $ module load psp-validation

At this point, ``psp`` command should be available, as well as compatible ``BGLibPy``, ``BluePy`` and ``neuron``, as well as compiled MOD files.

To ensure the result is reproducible, please consider using a specific `BBP archive S/W module <https://bbpteam.epfl.ch/project/spaces/display/BBPHPC/BBP+ARCHIVE+SOFTWARE+MODULES>`_.

pip install
-----------

Alternatively, ``psp-validation`` is also distributed as a Python package available at BBP devpi server:

.. code-block:: console

    $ pip install -i https://bbpteam.epfl.ch/repository/devpi/simple/ psp-validation

Only Python 2.7 / Python 3.5+ is supported at the moment.

Getting BGLibPy / Neuron dependencies configured might be not straightforward, please refer to BGLibPy `installation instructions <https://bbpcode.epfl.ch/documentation/BGLibPy-3.2/installation.html>`_ for the details.
