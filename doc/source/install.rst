Installation
============

module load
-----------

The easiest way to get ``psp-validation`` package is by using a module:

.. code-block:: console

    $ module purge
    $ module load $archive
    $ module load $model_specific_neurodamus
    $ module load psp-validation

Where ``$archive`` is either ``unstable`` for to get the latest, or a specific version.
To ensure the result is reproducible, please consider using a specific `BBP archive S/W module <https://bbpteam.epfl.ch/project/spaces/display/BBPHPC/BBP+ARCHIVE+SOFTWARE+MODULES>`_.

The ``$model_specific_neurodamus`` relates to ``NEURODAMUS Repository Reorganisation and Modules on BB5`` under `Loading Neurodamus <https://bbpteam.epfl.ch/project/spaces/display/BGLIB/NEURODAMUS+Repository+Reorganisation+and+Modules+on+BB5>`_.

At this point, ``psp`` command should be available, as well as compatible ``BGLibPy``, ``BluePy`` and ``neuron``, as well as compiled MOD files.


pip install
-----------

Alternatively, ``psp-validation`` is also distributed as a Python package available at BBP devpi server:

.. code-block:: console

    $ pip install -i https://bbpteam.epfl.ch/repository/devpi/simple/ psp-validation

Only Python 3.6+ is supported at the moment.

Getting BGLibPy / Neuron dependencies configured might be not straightforward, please refer to BGLibPy `installation instructions <https://bbpteam.epfl.ch/documentation/projects/BGLibPy/latest/installation.html>`_ for the details.
