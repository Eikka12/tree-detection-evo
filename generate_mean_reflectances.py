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

def generate_mean_reflectances(tile_fn, trees_in_tile):
    tile = rxr.open_rasterio(tile_fn)
    print(f'Processing tile {tile_fn}, {len(trees_in_tile)} trees to extract')
    means = []
    for tree in trees_in_tile.itertuples():
        xmin, ymin, xmax, ymax = tree.geometry.bounds
        cropped = tile.sel(y=slice(ymax, ymin),
                           x=slice(xmin, xmax)).copy()[:-1]
        for x,y in product(range(cropped.shape[2]), range(cropped.shape[1])):
            if not Point(cropped[:,y,x].x.values, cropped[:,y,x].y.values).within(tree.geometry):
                cropped[:,y,x] = np.nan
        means.append(np.nanmean(cropped, axis=(1,2)))    
    return means

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
    with multiprocessing.Pool(10) as pool:
        means = pool.starmap(generate_mean_reflectances, inputs)
    collated = None
    for m, i in zip(means, inputs):
        temp = pd.DataFrame(data=np.array(m), columns=[f'band_{b+1}' for b in range(460)])
        if collated is None:
            collated = pd.concat([i[1], temp], axis=1)
        else:
            temp = pd.concat([i[1], temp], axis=1)
            collated = pd.concat([collated, temp])

    collated.to_file(save_dir/'means.geojson')


if __name__ == "__main__":

    make_train_data("./data/matched/matched_trees.geojson", "./data/tiles", "./data/matched_w_features")