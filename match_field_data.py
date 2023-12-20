import sys
import os
import pandas as pd
import geopandas as gpd
from src import utils
from pathlib import Path

from fastcore.script import *

@call_parse
def generate_data_contour(field_measurements:Path, # Path to the file containing field measurements
                          tree_crown_dir:Path, # Path to the directory containing the segmented crowns  
                          output_directory:Path): # Where to save the results.
    """
    Main function for training data generation
    """
    
    # Read shapefile containing field measurements
    if os.path.splitext(field_measurements)[1] in ['.shp', '.geojson']:
        trees_shp = gpd.read_file(field_measurements)
    elif os.path.splitext(field_measurements)[1] == '.csv':
        trees_shp = pd.read_csv(field_measurements)
    else:
        print('Invalid file')
        sys.exit(1)
    trees_shp = trees_shp[['species', 'tree_X', 'tree_Y', 'DBH', 'nov_2019', 'sum_2019', 'is_gps']]
    trees_shp.drop_duplicates(['tree_X', 'tree_Y'], inplace=True)
    tiles = [tree_crown_dir/f for f in os.listdir(tree_crown_dir) if f.endswith('.geojson')]
    tree_shapes = None

    # Create outdir if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for t in tiles:
        # Extract tile_id
        tile_id = t.stem
        print(f'Processing tile {tile_id}')

        # Read delineated crowns from shp
        tile_lidar_detected = gpd.read_file(f'{tree_crown_dir}/{tile_id}.geojson')
        xdims = tile_lidar_detected.ttop_x.min(), tile_lidar_detected.ttop_x.max()
        ydims = tile_lidar_detected.ttop_y.min(), tile_lidar_detected.ttop_y.max()
        # Filter treetops
        tile_field_plot = trees_shp[trees_shp['tree_Y'].between(ydims[0], ydims[1]) & 
                                    trees_shp['tree_X'].between(xdims[0], xdims[1])].copy()
        if len(tile_field_plot) == 0:
            print(f'No measured trees in tile {tile_id}')
            continue
        
        tile_lidar_detected[['meas_x', 'meas_y', 'species', 'dbh', 'sum_2019', 'nov_2019', 'is_gps']] = tile_lidar_detected.apply(lambda row: utils.label_contours(row, tile_field_plot), axis=1, result_type='expand')
        tile_lidar_detected.dropna(inplace=True)
        # Match lidar and field plot trees
        if len(tile_lidar_detected) == 0:
            print(f'No detected trees in tile {tile_id}')
            continue
        print(f'{len(tile_lidar_detected)} remain after correction and drop')
        # Separate files for each tile
        tile_lidar_detected.to_file(filename=output_directory/f'{tile_id}.geojson', driver='GeoJSON')
        # Extract data cubes for each tree. Do not normalize any other channel except CHM one.
        for tree in tile_lidar_detected.itertuples():
            # Save tree information
            if tree_shapes is None:
                tree_shapes = gpd.GeoDataFrame([tree], crs=tile_lidar_detected.crs)
            else:
                tree_shapes = pd.concat([tree_shapes, gpd.GeoDataFrame([tree],crs=tile_lidar_detected.crs)])
    tree_shapes.drop('Index', inplace=True, axis=1)
    tree_shapes['filename'] = [f'{i}.npy' for i in range(len(tree_shapes))]
    # Finally save a data frame containing the information of all detected trees
    tree_shapes.to_file(filename=f'{output_directory}/matched_trees.geojson', driver='GeoJSON')
    return
