from fastcore.script import *
import os 
import re 
import geopandas as gpd
from shapely.geometry import Polygon
import multiprocessing
from pathlib import Path

def merge_files(ttop_fname:Path, crown_fname:Path, outfile:Path):
    "Read, merge and fix CRS"

    print(f'Processing files {ttop_fname} and {crown_fname}')
    ttops = gpd.read_file(ttop_fname)
    ttops.rename(columns={'geometry':'ttop', 'Z':'max_height'}, inplace=True)
    ttops.set_index('treeID', drop=True, inplace=True)
    ttops['ttop_x'] = ttops.apply(lambda row: row.ttop.x, axis=1)
    ttops['ttop_y'] = ttops.apply(lambda row: row.ttop.y, axis=1)
    ttops = ttops.drop(['ttop', 'max_height'], axis=1)
    # Open crowns
    crowns = gpd.read_file(crown_fname)
    crowns.set_index('value', drop=True, inplace=True)
    crowns.sort_values(by='value', inplace=True)
    # Join dataframes
    crowns = crowns.join(ttops, how='outer')
    crowns = crowns.dropna()
    
    # Fill holes in polygons.
    crowns['geometry'] = crowns.apply(lambda row: Polygon(row.geometry.exterior), axis=1)
    # Add treeID column back
    crowns.rename(columns={'value':'treeID'}, inplace=True)
    
    # Add information about bounding box shapes
    crowns['bounds_x'] = crowns.apply(lambda row: row.geometry.bounds[2] - row.geometry.bounds[0], axis=1)
    crowns['bounds_y'] = crowns.apply(lambda row: row.geometry.bounds[3] - row.geometry.bounds[1], axis=1)

    crowns.set_crs('EPSG:32635', inplace=True, allow_override=True)

    tile_id = outfile.stem

    crowns['tile_id'] = tile_id
    crowns.to_file(filename=outfile, driver='GeoJSON')
    return 


@call_parse
def fix_crown_data(path_to_treetops:Path, # Folder containing the treetops
                   path_to_crowns:Path, # Folder containing the crowns
                   outdir:Path): # Where to save the combined results
    "Fix CRS information and combine crowns and treetops to single files"
    if not os.path.exists(outdir): os.makedirs(outdir)
    fnames = os.listdir(path_to_treetops)
    inputs = [(path_to_treetops/f, path_to_crowns/f, outdir/f) for f in fnames]
    with multiprocessing.Pool(10) as pool:
        res = pool.starmap(merge_files, inputs)
