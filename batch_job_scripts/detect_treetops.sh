#!/bin/bash
#SBATCH --job-name=detect-treetops
#SBATCH --account=project_2001325
#SBATCH --time=12:00:00
#SBATCH --mem-per-cpu=5G
#SBATCH --partition=small
#SBATCH --cpus-per-task=20
#SBATCH --output=/scratch/project_2001325/evo_hyperspectral/logs/detect_trees_out_%j.txt
#SBATCH --error=/scratch/project_2001325/evo_hyperspectral/logs/detect_trees_err_%j.txt

#load modules
module load r-env

data_path=/scratch/project_2001325/evo_hyperspectral/data/tiles

# window size
ws=5

# minimum height
hmin=10

# output directory
outdir=/scratch/project_2001325/evo_hyperspectral/data/

# Specify a temp folder path
echo "TMPDIR=/scratch/project_2001325/evo_hyperspectral/temp" >> ~/.Renviron

# Run rscript with parameters
Rscript /scratch/project_2001325/evo_hyperspectral/detect_trees.R $data_path $ws $hmin $outdir --no-save
