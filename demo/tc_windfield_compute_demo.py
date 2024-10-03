#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 11:35:50 2024

This is a script to compute the TC wind field from the ECMWF forecast tracks.
Output: climada.hazard.Hazard class in .hdf5 format

@author: Pui Man (Mannie) Kam
"""

import time
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

from climada.hazard import TCTracks, TropCyclone
from climada_petals.hazard import TCForecast

from climada.util.api_client import Client
client = Client()

time_start = time.time()

SAVE_WIND_DIR = "./data/tc_wind/"

BUFR_TRACKS_FOLDER = "./data/20240825000000/"

CAT_NUMBER = {'Tropical Depression': -1,
              'Tropical Storm': 0,
              'Hurricane Cat. 1': 1,
              'Hurricane Cat. 2': 2,
              'Hurricane Cat. 3': 3,
              'Hurricane Cat. 4': 4,
              'Hurricane Cat. 5': 5}

def filter_storm(fcast):
    """
    

    Parameters
    ----------
    fcast : climada.TCForecast
        The set of forecast data from ECMWF

    Returns
    -------
    fcast_filter : climada.TCForecast
        TCForecast class with storms which are named storm

    """
    tr_name_list = [tr.name for tr in fcast.data]
    tr_name_list = list(set(tr_name_list))
    
    fcast_filter = TCTracks()

    for tr_name in tr_name_list:

        if tr_name[:2].isdigit():
            continue
        
        else:
            fcast_filter.append(fcast.subset({
                'name': tr_name
            }).data)
    
    
    return fcast_filter

# retrieve the Centroids from 
glob_centroids = client.get_centroids()

# retrieve the latest forecast
tr_fcast = TCForecast()
tr_fcast.fetch_ecmwf(path=BUFR_TRACKS_FOLDER)
tr_filter = filter_storm(tr_fcast)

tr_name_unique = set([tr.name for tr in tr_filter.data])

for tr_name in tr_name_unique:
    # select single storm and interpolate the tracks
    tr_one_storm = tr_filter.subset({'name': tr_name})
    tr_one_storm.equal_timestep(.5)

    # refine the centroids
    storm_extent = tr_one_storm.get_extent(deg_buffer=5.)
    centroids_refine = glob_centroids.select(extent=storm_extent)

    # compute the windfield for each storm
    tc_wind_one_storm = TropCyclone.from_tracks(tr_one_storm, centroids_refine)
    tc_wind_one_storm.write_hdf5(SAVE_WIND_DIR +'tc_wind_' +tr_name +'20240825000000.hdf5')

# record the time
time_end = time.time()

print("TC wind computation complete. Time: " +str(time_end-time_start))


