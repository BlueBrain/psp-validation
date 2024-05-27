File formats
============

.. _pathway-config:

Pathway config
--------------

Pathway config is a YAML file which defines:
    - pair selection criteria
    - simulation parameters
    - reference biological data (optionally)


Pair selection criteria
~~~~~~~~~~~~~~~~~~~~~~~

Defined in `pathway` group.

For debugging purposes, GID pairs could be defined explicitly:

.. code-block:: yaml

    pathway:
        pairs:
            - [42, 43]
            - [44, 45]
            - ...

But usually pairs are defined using `pre`- and `post`-synaptic cell group and optional `constraints`.

Cell groups refer either to a target defined in the circuit itself; or in additional cell group definition file (this one takes precedence over circuit-defined targets).

For example,

.. code-block:: yaml

    pathway:
        pre: L5_PC
        post: L5_BC

`null` could be used as a target name, and means "all cells".

`constraints` group (optional) specifies additional filtering criteria:

+-------------+-------+---------------------------------------+
| key         | type  | meaning                               |
+=============+=======+=======================================+
| unique_gids | bool  | don't use same GID twice              |
+-------------+-------+---------------------------------------+
| min_nsyn    | int   | min number of synapses per connection |
+-------------+-------+---------------------------------------+
| max_nsyn    | int   | max number of synapses per connection |
+-------------+-------+---------------------------------------+
| max_dist_x  | float | max distance along X axis             |
+-------------+-------+---------------------------------------+
| max_dist_y  | float | max distance along Y axis             |
+-------------+-------+---------------------------------------+
| max_dist_z  | float | max distance along Z axis             |
+-------------+-------+---------------------------------------+

Connections are queried from a specific `edge population` given as a commandline parameter (see: :ref:`Tutorial <Run_PSP>`).

Simulation parameters
~~~~~~~~~~~~~~~~~~~~~

`protocol` group consisting of the following keys:

+-----------+----------+-------------------------------------------+
| key       | type     | meaning                                   |
+===========+==========+===========================================+
| record_dt | float    | voltage trace recording step [ms]         |
+-----------+----------+-------------------------------------------+
| t_stop    | float    | simulation duration [ms]                  |
+-----------+----------+-------------------------------------------+
| t_stim    | float    | time(s) when presynaptic cell fires [ms]  |
|           | OR list  |                                           |
+-----------+----------+-------------------------------------------+
| hold_V    | float    | holding voltage [mV]                      |
+-----------+----------+-------------------------------------------+
| hold_I    | float    | holding current [mA]                      |
+-----------+----------+-------------------------------------------+
| post_ttx  | bool     | block Na channels of postsynaptic cell    |
|           |          | (optional; False if omitted)              |
+-----------+----------+-------------------------------------------+

.. warning::
   Setting both the ``hold_V`` and ``hold_I`` in current clamping mode is not supported:
   If ``hold_V: null``, holding current calculation will be skipped and ``hold_I`` will resolve to 0.
   As this might change in the future, it is better to set ``hold_I`` explicitly as 0 and not set ``hold_V`` at all.

Reference biological data
~~~~~~~~~~~~~~~~~~~~~~~~~

`reference` group consisting of the following keys:

+---------------+--------+-----------------------------------------+
| key           | type   | meaning                                 |
+===============+========+=========================================+
| author        | string | Reference publication                   |
+---------------+--------+-----------------------------------------+
| psp_amplitude | dict   | PSP amplitude mean / std                |
+---------------+--------+-----------------------------------------+
| synapse_count | dict   | Synapse count per connection mean / std |
+---------------+--------+-----------------------------------------+

Other
~~~~~

+---------------------+--------+------------------------------------------------------------+
| key                 | type   | meaning                                                    |
+=====================+========+============================================================+
| min_amplitude       | float  | Minimal PSP amplitude of the mean value to consider [mV].  |
|                     |        | Values below that are replaced with NaNs.                  |
|                     |        | Optional, defaults to 0.0.                                 |
+---------------------+--------+------------------------------------------------------------+
| min_trace_amplitude | float  | Minimal PSP amplitude of the traces to consider, relative  |
|                     |        | to the resting potential [mV].                             |
|                     |        | Traces that are completely below this value are considered |
|                     |        | synaptic failures and are filtered out.                    |
|                     |        | Optional, defaults to 0.0 (traces are not filtered out).   |
+---------------------+--------+------------------------------------------------------------+

Example
~~~~~~~

Putting it all together:

.. code-block:: console

    reference:
        author: "Markram 97"
        psp_amplitude:
            mean: 1.3
            std: 1.1
        synapse_count:
            mean: 5.5
            std: 1.1

    pathway:
        pre: L5_TTPC
        post: L5_TTPC
        constraints:
            unique_gids: true
            max_dist_x: 100.0
            max_dist_z: 100.0

    min_amplitude: 0.01
    min_trace_amplitude: 0.01

    protocol:
        record_dt: 0.1
        hold_V: -67.0
        t_stim: [700.0, 800.0]
        t_stop: 900.0
        post_ttx: false

Please refer to `usecases <https://github.com/BlueBrain/psp-validation/tree/main/usecases>`__ for more examples.


.. _target-definitions:

Target definitions
------------------

Additional targets defined as SNAP `node queries <https://github.com/BlueBrain/snap/blob/master/doc/source/notebooks/09_node_queries.ipynb>`__.

For example,

.. code-block:: console

    L4_EXC:
        layer: "4"
        synapse_class: "EXC"

corresponds to BluePy cell group

.. code-block:: python

    {"layer": "4", "synapse_class": "EXC"}


.. _summary-file:

Summary file
------------

Main output of ``psp run``; YAML file storing obtained PSP amplitudes mean / std.

If source pathway config specifies reference PSP amplitude data, it is repeated here, along with conductance scaling factor based on the ratio between model and reference data.

.. code-block:: yaml

    pathway: L5_TTPC-L5_TTPC
    model:
        mean: 1.37383798325
        std:  1.10050952095
    reference:
        mean: 1.3
        std:  1.1
    scaling: 0.94519076506

.. _trace-dump:

Trace dump
----------

On-request output of ``psp run``; HDF5 file storing voltage / current traces for each trial, as well as their average, for each simulated pair.
For voltage, spiking trials are filtered out when calculating average.

.. code-block:: none

    /traces
        /<pair1>
           /trials   [N x 2 x T]  # (v / i, t) for each of N trials
           /average  [2 x T]      # "averaged" (v / i, t)
        /<pair2>
            ...

Each `pair` group stores pre- and post-synaptic GIDs as `pre_gid` and `post_gid` attributes.
