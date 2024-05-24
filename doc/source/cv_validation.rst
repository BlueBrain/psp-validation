CV Validation
=============

``cv-validation`` command runs single cell simulations in `BlueCelluLab <https://bluecellulab.readthedocs.io/en/latest/>`__ to help calibrate NRRP to match
experimental coefficients of variation (CV) of PSP or PSC amplitudes.

It's a three-phase process consisting of setup, simulation and analysis (calibration).

Workflow
--------

.. _Setup:

Setup
~~~~~

Setup creates an output path and a directory named after the ``pathway`` in it.
In the pathway directory, it will create ``pairs.csv`` containing the pairs to simulate and the seeds for the random number generator.

The simulations are setup by providing the script with

*  `Simulation config <https://sonata-extension.readthedocs.io/en/latest/sonata_simulation.html>`__ file
*  :ref:`Target definition <target-definitions>` file
*  :ref:`Pathway config <pathway-config>` file
*  `Edge population <https://sonata-extension.readthedocs.io/en/latest/sonata_config.html#id4>`__ to evaluate
*  Number of SGID-TGID pairs to simulate
*  Output path
*  *(optional)* Seed used to initialize Numpy random number generator


Simulations can be set up as follows:

.. code-block:: bash

    module purge
    module load unstable neurodamus-neocortex psp-validation

    cv-validation [-v/-vv] setup \  # -v/-vv to add verbosity
        -c <simulation_config> \    # SONATA simulation config file
        -t <target_file> \          # Target File (see usecases/cv_validation/targets.yaml)
        -p <pathway_file> \         # Pathway File (see usecases/cv_validation/pathways)
        -e <edge_population> \      # Namee of the concerned edge population
        -n <number_of_pairs> \      # Number of pairs to simulate
        -o <output_dir>             # Output directory

    # OPTIONAL
        --seed <seed>  # Seed used to initialize Numpy random number generator
.. _Simulation:

Simulation
~~~~~~~~~~

Simulation outputs one ``.h5`` file per NRRP containing

*  Simulated pairs
*  Results of the simulation (points of time, soma voltages and currents)
*  Seeds used for random number generation

The structure of the ``.h5`` file is as follows:

.. code-block:: yaml

    sgid_tgid_pair:  # contains attribute 'seed' (same as in the csv file)
      RNG_seed_for_simulation:  # Seed used for the simulation
        time: [...]
        soma_voltage: [...]
        soma_current: [...]

Simulation uses the seeds and pairs from the file created in :ref:`Setup <Setup>`.
A few parameters are given to the simulation

*  Simulation config file (same as in :ref:`Setup <Setup>`)
*  Pathway file (same as in :ref:`Setup <Setup>`)
*  NRRP range to simulate
*  Number of simulations to do (per pair)
*  Output path (same as in :ref:`Setup <Setup>`)
*  *(optional)* Clamp to apply
*  *(optional)* Number of parallel jobs (if not set, trials are run sequentially)

To run the simulation:

.. code-block:: bash

    module purge
    module load unstable neurodamus-neocortex psp-validation

    cv-validation [-v/-vv] run \  # -v/-vv to add verbosity
        -c <simulation_config> \  # SONATA simulation config file
        -r <num_trials> \         # Number of simulations for each pair
        --nrrp <NRRP_RANGE> \     # NRRP range given as <min_nrrp> <max_nrrp>
        -p <pathway_file> \       # Pathway File (see usecases/cv_validation/pathways)
        -o <output_dir>           # Output directory

    # OPTIONAL
        -m <clamp>  # Clamp to apply: 'voltage' or 'current' (Default: 'current')
        -j <jobs>   # Number of parallel jobs to run (Default: None -> run sequentially)

    # Simulation is the longest out of the three steps. To speed up the execution,
    # the NRRP range can be divided and run in different computing nodes.
    # E.g., instead of
    cv-validation run ... --nrrp 1 14
    # you can do run the following two (in different nodes)
    cv-validation run ... --nrrp 1 7
    cv-validation run ... --nrrp 8 14

Analysis
~~~~~~~~

This phase analyses the results in the ``.h5`` files obtained in the simulation phase and outputs
the computed optimal NRRP based on the simulated runs.

The optimal NRRP is acquired by analysing the CVs and Jackknife sampled CVs (JKCV) of the PSP/PSC amplitudes of the
simulated pairs using a Monte Carlo-like optimization.

In a nutshell this is done as follows:

#. create so-called intermediate lambda values for the given NRRP range
#. draw NRRPs from a Poisson distribution for each lambda
#. calculate the mean CV and mean JKCV for each lambda based on the drawn NRRPs
#. find which lambda minimizes the difference between the mean CV/JKCV and the target CV/JKCV

The analysis code also plots the CV regression as well as the CVs and Jackknife CVs against the calculated lambdas.
These will be found in a subdirectory named after the used pathway in the given output path.

Parameters passed to the analysis script:

*  Pathway file used in :ref:`Simulation <Simulation>`
*  NRRP range used in :ref:`Simulation <Simulation>`
*  Output path (same as in :ref:`Setup <Setup>`)
*  *(optional)* Number of pairs to randomly select out of all simulated pairs (Default: n_simulated/2)
*  *(optional)* Number of repetitions for random NRRP generation (Default: 50)
*  *(optional)* Number of parallel jobs (if not set, trials are run sequentially)

Analysis/calibration can be run with:

.. code-block:: bash

    module purge
    module load unstable neurodamus-neocortex psp-validation

    cv-validation [-v/-vv] calibrate \  # -v/-vv to add verbosity
        -p <pathway_file> \             # Pathway File (see usecases/cv_validation/pathways)
        --nrrp <NRRP_RANGE> \           # NRRP range given as <min_nrrp> <max_nrrp>
        -o <output_dir>                 # Output directory

    # OPTIONAL
        -n <num_pairs>   # number of pairs to randomly select out of all pairs (Default: n_simulated/2)
        -r <num_reps>    # number of repetitions for random NRRP generation (Default: 50)
        -j <jobs>        # Number of parallel jobs to run (Default: None -> run sequentially)

