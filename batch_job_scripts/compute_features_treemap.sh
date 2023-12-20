#!/bin/bash
#SBATCH --job-name=compute_features
#SBATCH --account=project_2001325
#SBATCH --time=15:00:00
#SBATCH --mem-per-cpu=4G
#SBATCH --partition=small
#SBATCH --mail-type=END
#SBATCH --cpus-per-task=30
#SBATCH --output=/scratch/project_2001325/evo_hyperspectral/logs/compute_features_treemap_out_%j.txt
#SBATCH --error=/scratch/project_2001325/evo_hyperspectral/logs/compute_features_treemap_err_%j.txt

# activate environment and load module
module purge
module load tykky

export PATH="/projappl/project_2001325/ibccarbon/bin:$PATH"

scratchdir=/scratch/project_2001325/evo_hyperspectral/

cd $scratchdir/
# set parameters for preprocessing
tree_dir=$scratchdir/data/treemap/merged/
tile_dir=$scratchdir/data/tiles/
save_dir=$scratchdir/data/treemap/segs_w_features/

# Compute the features for each matched tree segment
python generate_features_treemap.py $tree_dir $tile_dir $save_dir
