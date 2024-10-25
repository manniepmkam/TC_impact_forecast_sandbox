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

from plot_func import plot_global_tracks

client = Client()

time_start = time.time()

SAVE_WIND_DIR = "./data/tc_wind/"

BUFR_TRACKS_FOLDER = "./data/20240825000000/"

# We use the traditional WMO guidelines for converting between various wind averaging periods
# in tropical cyclone conditions (cf. https://library.wmo.int/doc_num.php?explnum_id=290)
# Our input data is giving the maximum sustained wind speed for ten minute intervals while we need it for one minute
# intervals. In one minute intervals, changes in wind speed are more pronounced, so we need to make the maximum
# sustained wind speed slightly bigger.
WIND_CONVERSION_FACTOR = 1. / 0.88

def filter_storm(fcast: TCForecast):
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

def _correct_max_sustained_wind_speed(tc_forecast: TCForecast,
                                      wind_conversion_factor: float = WIND_CONVERSION_FACTOR) -> None:
    """
    Converts the maximum sustained wind speed by a given factor. The sustained wind speed is defined as the wind speed
    which has not been underrun by any measurement within a given time interval.
    Note that the operation of multiplying by a constant factor is simplifying reality and a more complex method
    should be used eventually
    :param tc_forecast: The tracks object to which the modification is applied
    :param wind_conversion_factor: The factor by which the maximum sustained wind will be modified
    :return:
    """
    for dataset in tc_forecast.data:
        dataset['max_sustained_wind'] *= wind_conversion_factor

# retrieve the Centroids from 
glob_centroids = client.get_centroids()

# retrieve the latest forecast
tr_fcast = TCForecast()
tr_fcast.fetch_ecmwf(path=BUFR_TRACKS_FOLDER)
tr_filter = filter_storm(tr_fcast)
tr_filter.equal_timestep(.5)
_correct_max_sustained_wind_speed(tr_filter)

fig = plot_global_tracks(tr_filter).get_figure().savefig('./tracks_20240825000000.png')

tr_name_unique = set([tr.name for tr in tr_filter.data])

for tr_name in tr_name_unique:
    # select single storm and interpolate the tracks
    tr_one_storm = tr_filter.subset({'name': tr_name})

    # refine the centroids
    storm_extent = tr_one_storm.get_extent(deg_buffer=5.)
    centroids_refine = glob_centroids.select(extent=storm_extent)

    # compute the windfield for each storm
    tc_wind_one_storm = TropCyclone.from_tracks(tr_one_storm, centroids_refine)
    tc_wind_one_storm.write_hdf5(SAVE_WIND_DIR +'tc_wind_' +tr_name +'_20240825000000.hdf5')

# record the time
time_end = time.time()

print("TC wind computation complete. Time: " +str(time_end-time_start))