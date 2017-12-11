Cookbook
========

Batch processing
----------------

To process multiple pathway configs in parallel, it could be handy to combine Slurm with `GNU Parallel <https://www.gnu.org/software/parallel/>`_ with `sbatch` script like:

.. code-block:: bash

    #!/bin/sh

    #SBATCH --job-name="psp"
    #SBATCH --time=8:00:00
    #SBATCH --mem=64000
    #SBATCH --output=%LOGS_DIR%/stdout.log
    #SBATCH --error=%LOGS_DIR%/stderr.log
    #SBATCH --partition=prod
    #SBATCH --account=proj64
    #SBATCH --nodes=8
    #SBATCH --ntasks-per-node=1
    #SBATCH --cpus-per-task=16
    #SBATCH --exclusive

    source /gpfs/bbp.cscs.ch/scratch/gss/nse/psp-validation/setenv_sscx.sh

    # --delay 0.2 prevents overloading the controlling node
    parallel="parallel --delay 0.2 -j $SLURM_NTASKS --joblog %LOGS_DIR%/runtask.log"

    EXEC_CMD="psp -vv run \
        -c %CircuitConfig% \
        -t %TARGETS% \
        -o %OUTPUT_DIR% \
        -n %NUM_PAIRS% \
        -r %NUM_TRIALS% \
        --dump-traces \
        --dump-amplitudes \
        --seed %SEED% \
        --jobs $SLURM_CPUS_PER_TASK"

    $parallel "srun --exclusive -N1 -n1 $EXEC_CMD {1} >& %LOGS_DIR%/job-{#}.log" ::: %PATHWAYS%