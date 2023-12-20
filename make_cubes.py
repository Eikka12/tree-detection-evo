from fastcore.script import *
import os
import rioxarray as rxr
import numpy as np 
import geopandas as gpd
from shapely.geometry import Point
from itertools import product
import multiprocessing
from pathlib import Path

def generate_cubes_from_tile(tile_fn, trees_in_tile, save_dir, ws, delineate=False, normalize=False):
    tile = rxr.open_rasterio(tile_fn)
    print(f'Processing tile {tile_fn}, {len(trees_in_tile)} trees to extract')
    for tree in trees_in_tile.itertuples():
        cropped = tile.sel(y=slice(tree.ttop_y + ws, tree.ttop_y - ws ),
                           x=slice(tree.ttop_x - ws,  tree.ttop_x + ws)).copy()
        if cropped.shape[1] != ws*4 + 1: continue

        if cropped.shape[2] != ws*4 + 1: continue
        if delineate:
            for x,y in product(range(cropped.shape[2]), range(cropped.shape[1])):
                if not Point(cropped[:,y,x].x.values, cropped[:,y,x].y.values).within(tree.geometry):
                    cropped[:,y,x] = np.nan
        np.save(f'{save_dir}/{tree.filename}', cropped.values)
    return

@call_parse
def make_train_data(tree_path:Path, # Path to the file containing the matched trees
                    tile_dir:Path, # Directory for the hyperspectral data 
                    save_dir:Path, # Where to save the resulting files
                    delineate:bool, # Whether to mask all data outside the crown. 
                    window_size:int=4): # Radius of the squares extracted around treetops
    """
    Extract individual data cube files based on detected trees
    """
    # We have a preprocessed dataframe containing the trees
    if not os.path.exists(save_dir): os.makedirs(save_dir, exist_ok=True)
    all_trees = gpd.read_file(tree_path)
    inputs = [(f'{tile_dir}/{t}.tif', all_trees[all_trees.tile_id == t], 
              save_dir, window_size, delineate) for t in all_trees.tile_id.unique()]
    with multiprocessing.Pool(10) as pool:
        pool.starmap(generate_cubes_from_tile, inputs)
    return
