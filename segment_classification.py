from fastcore.script import *
import os
import numpy as np
import geopandas as gpd
import pandas as pd
from pathlib import Path
from fastai.tabular.all import *
import multiprocessing
from itertools import repeat

def predict_species(features:pd.DataFrame, 
                    learner:TabularLearner):
    """
    Predicts the species for a set of observations.

    Parameters
    ----------
    features : A DataFrame containing observations
    learner : A fastai tabular learner

    Return
    ------
    preds : A numpy array containing the predictions for each observation
    """

    # Create a dataloader for the data
    dl = learner.dls.test_dl(features)
    
    # Predict and convert predictions to a numpy array
    _, _, decoded = learner.get_preds(dl=dl, with_decoded=True)
    return np.array(dl.vocab[decoded])


def process_file(data_fn:Path,
                 learner:TabularLearner,
                 out_dir:Path):
    """
    Processes a single file of observations.

    Extracts the species for each segment in the given geodataframe file. 
    Adds the extracted species to the geodataframe, and removes the features 
    used for predicting. Stores the modified geodataframe as a geojson file in 
    the given output directory.

    Parameters
    ----------
    data_fn : A filepath to a parquet file containing a geodataframe
    learner : A fastai tabular learner used for prediction
    out_dir : The output directory
    """

    print(f"Processing tile {data_fn.stem}")
    
    # Read the tree segments
    data = gpd.read_parquet(data_fn)
    info = data.iloc[:,:10]
    features = data.iloc[:,10:]

    # Predict the species for each segment
    info["species"] = predict_species(features, learner)

    # Write the data (excluding the features) to a geojson
    info.to_file(out_dir/f"{data_fn.stem}.geojson", driver="GeoJSON")

    print(f"Finished with tile {data_fn.stem}")

@call_parse
def batch_inference(data_dir:Path,
                    learner_path:Path,
                    out_dir:Path,
                    num_workers:int = 1):

    """
    Extracts the tree species for each tile in the given folder of data.

    Parameters
    ----------
    data_dir : A directory containing the tree segments in each tile
    learner_path : A filepath to the learner used for prediction
    out_dir : The directory in which the processed data is stored
    """

    # Create the output directory if it does not exist
    if not os.path.exists(out_dir): os.makedirs(out_dir, exist_ok=True)

    data_fns = [data_dir/f for f in os.listdir(data_dir)]
    learner = load_learner(learner_path)

    with multiprocessing.Pool(num_workers) as pool:
        pool.starmap(process_file, zip(data_fns, repeat(learner), repeat(out_dir)))
        
