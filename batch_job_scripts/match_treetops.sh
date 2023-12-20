#!/bin/bash
#SBATCH --job-name=match-treetops
#SBATCH --account=project_2001325
#SBATCH --time=03:00:00
#SBATCH --mem-per-cpu=4G
#SBATCH --partition=small
#SBATCH --mail-type=END
#SBATCH --cpus-per-task=4
#SBATCH --output=/scratch/project_2001325/evo_hyperspectral/logs/match_treetops_out_%j.txt
#SBATCH --error=/scratch/project_2001325/evo_hyperspectral/logs/match_treetops_err_%j.txt

# activate environment and load module
module load tykky 

export PATH="/projappl/project_2001325/ibccarbon/bin:$PATH"

scratchdir=/scratch/project_2001325/evo_hyperspectral/

cd $scratchdir/
# set parameters for preprocessing
ttop_path=$scratchdir/data/ttops/
crown_path=$scratchdir/data/crowns/
merged_path=$scratchdir/data/merged/

# Run match treetops and delineations
python fix_crown_data.py $ttop_path $crown_path $merged_path

# set parameters for tree matching
field_data=$scratchdir/data/field_data/all_trees_w_deadwood.shp
out_dir=$scratchdir/data/matched

# Run tree detection
python match_field_data.py $field_data $merged_path $out_dir
