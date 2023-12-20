from fastcore.script import *
import os
import rioxarray as rxr
import numpy as np 
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from itertools import product, repeat
import multiprocessing
from pathlib import Path
from scipy.stats import skew, kurtosis

def generate_reflectance_features(tile_fn, trees_in_tile):
    tile = rxr.open_rasterio(tile_fn)

    means = []
    sds = []
    mins = []
    maxs = []
    skews = []
    kurts = []

    for tree in trees_in_tile.itertuples():
        xmin, ymin, xmax, ymax = tree.geometry.bounds

        # Extract pixels from within the bounding box of the current tree
        cropped = tile.sel(y=slice(ymax, ymin),
                           x=slice(xmin, xmax)).copy()

        # Set pixels outside the tree to nan
        for x,y in product(range(cropped.shape[2]), range(cropped.shape[1])):
            if not Point(cropped[:,y,x].x.values, cropped[:,y,x].y.values).within(tree.geometry):
                cropped[:,y,x] = np.nan
                
        means.append(np.nanmean(cropped, axis=(1,2)))    
        sds.append(np.nanstd(cropped, axis=(1,2)))
        mins.append(np.nanmin(cropped, axis=(1,2)))
        maxs.append(np.nanmax(cropped, axis=(1,2)))
        skews.append(skew(cropped, axis=(1,2), nan_policy = "omit"))
        kurts.append(kurtosis(cropped, axis=(1,2), nan_policy = "omit"))
    
    # Stack all trees and features into a single dataframe
    prefixes = ['mean_', 'sd_', 'min_', 'max_', 'skew_', 'kurt_']
    subs = [f'band_{b+1}' for b in range(461)]
    colnames = np.hstack([[prefix + sub for sub in subs] for prefix in prefixes])
    features = np.hstack([np.array(feature) for feature in (means, sds, mins, maxs, skews, kurts)])
    features = pd.DataFrame(data=features, columns=colnames)

    # Replace NaNs with feature means
    features.fillna(features.mean(), inplace=True)
    
    return features

def process_single_tile(tree_fn:Path, # Path to a file containing tree segments
                        tile_fn:Path, # Path to a file containing a hyperspectral tile
                        save_dir:Path): # The directory for storing the data
    """ 
    A helper function computing and storing features for a single tile.
    """
    print(f'Processing tile {tile_fn.stem}')
    
    # Read the tree segments
    trees_in_tile = gpd.read_file(tree_fn)

    # Compute the features
    features = generate_reflectance_features(tile_fn, trees_in_tile)

    # Merge the features with the tree segments
    collated = pd.concat([trees_in_tile, features.set_index(trees_in_tile.index)], axis = 1)

    collated.to_parquet(save_dir/f"{tree_fn.stem}.parquet")

    print(f'Finished with tile {tile_fn.stem}')

@call_parse
def make_train_data(tree_dir:Path, # Directory containing the tree segments
                    tile_dir:Path, # Directory for the hyperspectral data 
                    save_dir:Path): # Where to save the resulting files
    """
    Extract individual data cube files based on detected trees
    """
    
    # Create the output directory if it does not exist
    if not os.path.exists(save_dir): os.makedirs(save_dir, exist_ok=True)

    tree_fns = [tree_dir/f for f in os.listdir(tree_dir)]
    tile_fns = [tile_dir/f"{Path(f).stem}.tif" for f in os.listdir(tree_dir)]
    save_dirs = [save_dir] * len(tile_fns)

    # Go through each tile and compute the features for each tree in the tile
    inputs = zip(tree_fns,tile_fns,repeat(save_dir))
    with multiprocessing.Pool(30) as pool:
        pool.starmap(process_single_tile, inputs)

 

