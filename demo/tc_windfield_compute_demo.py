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
import warnings
warnings.filterwarnings("ignore")

from climada.hazard import TropCyclone
from climada_petals.hazard import TCForecast

from climada.util.api_client import Client
client = Client()

time_start = time.time()

SAVE_WIND_DIR = "../../data/tc_wind/"

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
        Filtered storm with at lease 1 member forecasted Tropical Storm cat. or above

    """
    sid_list = [tr.sid for tr in fcast.data]
    sid_list = list(set(sid_list))
    
    fcast_filter = TCForecast()
    
    for sid in sid_list:
        single_storm = [tr for tr in fcast.data if tr.sid==sid]
        
        cat = np.array([CAT_NUMBER[tr.category] for tr in single_storm])
        
        if np.any(cat>=0):
            fcast_filter.data.extend(single_storm)
        else:
            continue
    
    return fcast_filter

# retrieve the Centroids from 
glob_centroids = client.get_centroids()

# retrieve the latest forecast
tr_fcast = TCForecast()
tr_fcast.fetch_ecmwf()
tr_filter = filter_storm(tr_fcast)

# compute the windspeed
tc_wind = TropCyclone.from_tracks(tr_filter, glob_centroids)

tc_wind.write_hdf5(SAVE_WIND_DIR +"test_run.hdf5")

time_end = time.time()

print("TC wind computation complete. Time:" +str(time_end-time_start))


