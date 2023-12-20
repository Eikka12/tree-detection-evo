#!/bin/bash
#SBATCH --job-name=predict_species
#SBATCH --account=project_2001325
#SBATCH --time=05:00:00
#SBATCH --mem-per-cpu=4G
#SBATCH --partition=small
#SBATCH --mail-type=END
#SBATCH --cpus-per-task=10
#SBATCH --output=/scratch/project_2001325/evo_hyperspectral/logs/predict_species_out_%j.txt
#SBATCH --error=/scratch/project_2001325/evo_hyperspectral/logs/predict_species_err_%j.txt

# activate environment and load module
module purge
module load tykky 

export PATH="/projappl/project_2001325/ibccarbon/bin:$PATH"

scratchdir=/scratch/project_2001325/evo_hyperspectral/

cd $scratchdir/
# set parameters for preprocessing
data_dir=$scratchdir/data/treemap/segs_w_features/
learner_path=$scratchdir/models/deadwood_model.pkl
out_dir=$scratchdir/data/treemap/segs_w_species/


# Compute the features for each matched tree segment
python segment_classification.py $data_dir $learner_path $out_dir --num_workers 10