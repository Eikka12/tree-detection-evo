#!/bin/bash
#SBATCH --job-name=compute_features
#SBATCH --account=project_2001325
#SBATCH --time=05:00:00
#SBATCH --mem-per-cpu=4G
#SBATCH --partition=small
#SBATCH --mail-type=END
#SBATCH --cpus-per-task=20
#SBATCH --output=/scratch/project_2001325/evo_hyperspectral/logs/compute_features_out_%j.txt
#SBATCH --error=/scratch/project_2001325/evo_hyperspectral/logs/compute_features_err_%j.txt

# activate environment and load module
module purge
module load tykky 

export PATH="/projappl/project_2001325/ibccarbon/bin:$PATH"

scratchdir=/scratch/project_2001325/evo_hyperspectral/

cd $scratchdir/
# set parameters for preprocessing
tree_path=$scratchdir/data/matched/matched_trees.geojson
tile_path=$scratchdir/data/tiles/
out_path=$scratchdir/data/matched_w_features/

# Compute the features for each matched tree segment
python generate_features.py $tree_path $tile_path $out_path