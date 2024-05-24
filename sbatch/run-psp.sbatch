#!/bin/sh

#SBATCH --job-name="psp"
#SBATCH --output="psp-%j.out"
#SBATCH --time=4:00:00
#SBATCH --mem=64G
#SBATCH --partition=prod
#SBATCH --account=proj64
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16

module purge
module load unstable neurodamus-hippocampus psp-validation

CMD="psp -vv run --jobs $SLURM_CPUS_PER_TASK $@"
echo $CMD

srun $CMD
