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
To ensure the result is reproducible, please consider using a specific `BBP archive S/W module <https://bbpteam.epfl.ch/project/spaces/display/BBPHPC/BBP+ARCHIVE+SOFTWARE+MODULES>`__.

The ``$model_specific_neurodamus`` relates to ``NEURODAMUS Repository Reorganisation and Modules on BB5`` under `Loading Neurodamus <https://bbpteam.epfl.ch/project/spaces/display/BGLIB/NEURODAMUS+Repository+Reorganisation+and+Modules+on+BB5>`__.

At this point, ``psp`` command should be available, as well as compatible ``BlueCelluLab``, ``SNAP`` and ``neuron``, as well as compiled MOD files.


pip install
-----------

Alternatively, ``psp-validation`` is also distributed as a Python package:

.. code-block:: console

    $ pip install psp-validation

Currently, Python 3.7+ is supported.

Getting BlueCelluLab / Neuron dependencies configured might be not straightforward, please refer to BlueCelluLab `installation instructions <https://bluecellulab.readthedocs.io/en/latest/>`__ for the details.
