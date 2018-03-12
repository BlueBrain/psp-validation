Cookbook
========

Batch processing
----------------

One-node allocation
~~~~~~~~~~~~~~~~~~~

Using `sbatch` script like:

.. literalinclude:: ../../sbatch/run-psp.sbatch
   :language: bash

one can schedule a run for a single pathway like:

.. code-block:: bash

    $ sbatch run.sbatch -c %CIRCUIT% -t %TARGETS% -o %OUTPUT_DIR% -n %NUM_PAIRS% -r %NUM_TRIALS% --dump-traces --dump-amplitudes %PATHWAY%

.. note::

    Please don't forget to use custom ``neurodamus`` version if needed (e.g., ``neurodamus-hippocampus``).

To schedule all pathways from %PATHWAY_DIR%, make use of shell loop:

.. code-block:: bash

    for p in $(find %PATHWAY_DIR% -name "*.yaml")
    do
       sbatch run.sbatch ... $p
    done


Multi-node allocation
~~~~~~~~~~~~~~~~~~~~~

One way to execute set of pathways on multi-node allocation, is to combine Slurm with `GNU Parallel <https://www.gnu.org/software/parallel/>`_ using `sbatch` script like:

.. literalinclude:: ../../sbatch/run-psp-parallel.sbatch.template
   :language: bash

.. note::

    Please ensure you should have ``parallel`` tool somewhere in ``$PATH``.