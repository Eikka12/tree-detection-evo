from fastcore.script import *
import os
import rioxarray as rxr
import numpy as np 
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from itertools import product
import multiprocessing
from pathlib import Path
from scipy.stats import skew, kurtosis

def generate_reflectance_features(tile_fn, trees_in_tile):
    tile = rxr.open_rasterio(tile_fn)
    print(f'Processing tile {tile_fn}, {len(trees_in_tile)} trees to extract')
    means = []
    sds = []
    mins = []
    maxs = []
    skews = []
    kurts = []
    for tree in trees_in_tile.itertuples():
        xmin, ymin, xmax, ymax = tree.geometry.bounds
        cropped = tile.sel(y=slice(ymax, ymin),
                           x=slice(xmin, xmax)).copy()
        for x,y in product(range(cropped.shape[2]), range(cropped.shape[1])):
            if not Point(cropped[:,y,x].x.values, cropped[:,y,x].y.values).within(tree.geometry):
                cropped[:,y,x] = np.nan
        means.append(np.nanmean(cropped, axis=(1,2)))    
        sds.append(np.nanstd(cropped, axis=(1,2)))
        mins.append(np.nanmin(cropped, axis=(1,2)))
        maxs.append(np.nanmax(cropped, axis=(1,2)))
        skews.append(skew(cropped, axis=(1,2), nan_policy = "omit"))
        kurts.append(kurtosis(cropped, axis=(1,2), nan_policy = "omit"))
        
    return means,sds,mins,maxs,skews,kurts

@call_parse
def make_train_data(tree_path:Path, # Path to the file containing the matched trees
                    tile_dir:Path, # Directory for the hyperspectral data 
                    save_dir:Path): # Where to save the resulting files
    """
    Extract individual data cube files based on detected trees
    """
    # We have a preprocessed dataframe containing the trees
    if not os.path.exists(save_dir): os.makedirs(save_dir, exist_ok=True)
    all_trees = gpd.read_file(tree_path)
    inputs = [(f'{tile_dir}/{t}.tif', all_trees[all_trees.tile_id == t],) for t in all_trees.tile_id.unique()]
    with multiprocessing.Pool(20) as pool:
        features = pool.starmap(generate_reflectance_features, inputs)
    collated = None
    for fs, i in zip(features, inputs):
        data = np.hstack([np.array(feature) for feature in fs])
        prefixes = ['mean_', 'sd_', 'min_', 'max_', 'skew_', 'kurt_']
        subs = [f'band_{b+1}' for b in range(461)]
        colnames = np.hstack([[prefix + sub for sub in subs] for prefix in prefixes])
        temp = pd.DataFrame(data=data, columns=colnames)
        if collated is None:
            collated = pd.concat([i[1], temp.set_index(i[1].index)], axis=1)
        else:
            temp = pd.concat([i[1], temp.set_index(i[1].index)], axis=1)
            collated = pd.concat([collated, temp])
    
    print("Writing collated file")
    collated.to_parquet(save_dir/'features.parquet')
    #collated.to_file(save_dir/'features.geojson')
