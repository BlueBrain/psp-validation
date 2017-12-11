File formats
============

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
| max_dist_x  | float | max distance along X axis             |
+-------------+-------+---------------------------------------+
| max_dist_y  | float | max distance along Y axis             |
+-------------+-------+---------------------------------------+
| max_dist_z  | float | max distance along Z axis             |
+-------------+-------+---------------------------------------+

To query connections from a specific `projection` rather than main connectome, please add `projection` key:

.. code-block:: yaml

    pathway:
        projection: Thalamocortical_input_VPM
        pre: null
        post: L4_EXC

    ...


Simulation parameters
~~~~~~~~~~~~~~~~~~~~~

`protocol` group consisting of the following keys:

+-----------+-------+-------------------------------------------+
| key       | type  | meaning                                   |
+===========+=======+===========================================+
| record_dt | float | voltage trace recording step, ms          |
+-----------+-------+-------------------------------------------+
| t_stop    | float | simulation duration, ms                   |
+-----------+-------+-------------------------------------------+
| t_stim    | float | time(s) when presynaptic cell fires, [ms] |
+-----------+-------+-------------------------------------------+
| hold_V    | float | holding voltage, mV                       |
|           |       | (optional; None if omitted)               |
+-----------+-------+-------------------------------------------+
| post_ttx  | bool  | block Na channels of postsynaptic cell    |
|           |       | (optional; False if omitted)              |
+-----------+-------+-------------------------------------------+

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

    protocol:
        record_dt: 0.1
        hold_V: -67.0
        t_stim: 800.0
        t_stop: 900.0
        post_ttx: false

Please refer to `usecases <https://bbpcode.epfl.ch/source/xref/nse/psp-validation/usecases/>`_ for more examples.


Target definitions
------------------

Additional targets defined as BluePy.v2 `cell groups <https://bbpcode.epfl.ch/documentation/bluepy-0.11.9/tutorial.html#v2-cells-get>`_.

For example,

.. code-block:: console

    L4_EXC:
        layer: 4
        synapse_class: EXC

corresponds to BluePy.v2 cell group

.. code-block:: python

    {Cell.LAYER: 4, Cell.SYNAPSE_CLASS: 'EXC'}


Summary file
------------

Main output of `\`psp run\``; YAML file storing obtained PSP amplitudes mean / std.

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

Voltage traces
--------------

On-request output of `\`psp run\``; HDF5 file storing voltage traces, as well as their filtered average, for each simulated pair.

.. code-block:: none

    /traces
        /<pair1>
           /trials   [N x 2 x T]  # (v, t) for each of N trials
           /average  [2 x T]      # "averaged" (v, t)
        /<pair2>
            ...

Each `pair` group stores pre- and post-synaptic GIDs as `pre_gid` and `post_gid` attributes.
