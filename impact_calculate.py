#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 2 10:45:50 2024

This is a script to compute the TC wind field from the ECMWF forecast tracks.
Output: climada.hazard.Hazard class in .hdf5 format

@author: Pui Man (Mannie) Kam
"""
import warnings
warnings.filterwarnings("ignore")

import os
import glob
import numpy as np
import pandas as pd

from climada.hazard import Hazard
from climada.engine import ImpactCalc
from climada.util.coordinates import get_country_code, country_to_iso
from climada.util.api_client import Client
client = Client()

from impact_calc_func import (
    impf_set_exposed_pop, impf_set_displacement,
    round_to_previous_12h_utc, get_forecast_times,
    get_tc_wind_files, summarize_forecast,
    save_forecast_summary, make_save_summary_filename
)

# Save directories
SAVE_DIR = "./test_dir/"

# get the wind files
TC_WIND_DIR = "./demo/data/tc_wind" # change to a scratch folder

# Get the current timestamp
# current_timestamp = pd.Timestamp.now().tz_localize('UTC')
current_timestamp = pd.Timestamp('2024-08-25 02:00', tz='UTC')

forecast_time, previous_forecast_time = get_forecast_times(current_timestamp)
tc_wind_files = get_tc_wind_files(forecast_time, previous_forecast_time, TC_WIND_DIR)

if not tc_wind_files:
    print(f"No TC activities at {forecast_time.strftime('%Y-%m-%d_%HUTC')}.")
    print("End impact calculation script")
    exit()

# Now start the impact calculation for all the storms
for tc_file in tc_wind_files:


    # extract the tc_name from the hdf file
    tc_base_file_name = os.path.basename(tc_file)
    tc_name = tc_base_file_name.split('_')[2]

    # read the hdf file
    tc_haz = Hazard.from_hdf5(tc_file)

    # get the country code where the wind speed >0
    idx_non_zero_wind = tc_haz.intensity.max(axis=0).nonzero()[1]
    country_code_all = get_country_code(
                            tc_haz.centroids.lat[idx_non_zero_wind], 
                            tc_haz.centroids.lon[idx_non_zero_wind]
                        )
    country_code_unique = np.trim_zeros(np.unique(country_code_all))

    # now run impact for each country
    for country_code in country_code_unique:

        country_iso3 = country_to_iso(country_code, "alpha3")
        try:
            exp = client.get_exposures(exposures_type='litpop',
                                    properties={'country_iso3num':[str(country_code)],
                                                'exponents':'(0,1)',
                                                'fin_mode':'pop',
                                                'version':'v2'
                                                }
                                    )
        except client.NoResult:
            print(f"there is no matching dataset in Data API. Country code: {country_code}")
            continue

        # run impact calc for people exposed to cat. 1 wind speed or above
        impf_exposed = impf_set_exposed_pop()

        impact_exposed = ImpactCalc(exp, impf_exposed, tc_haz).impact()

        if impact_exposed.aai_agg == 0.: # do not save the files if impact is 0.
            continue

        imp_exposed_summary = summarize_forecast(country_iso3=country_to_iso(country_code, 
                                                                     "alpha3"),
                                        forecast_time=forecast_time.strftime('%Y-%m-%d_%HUTC'),
                                        impact_type="exposed_population_32.92ms",
                                        tc_haz=tc_haz,
                                        tc_name=tc_name,
                                        impact=impact_exposed)

        save_forecast_summary(imp_exposed_summary, 
            SAVE_DIR +make_save_summary_filename(imp_exposed_summary))

        # run the same impact calc but for displacement
        impf_displacement = impf_set_displacement(country_iso3)

        impact_displacement = ImpactCalc(exp, impf_displacement, tc_haz).impact()

        if impact_displacement.aai_agg == 0.: # do not save the files if impact is 0.
            continue
        imp_displacement_summary = summarize_forecast(country_iso3=country_to_iso(country_code, 
                                                                     "alpha3"),
                                                    forecast_time=forecast_time.strftime('%Y-%m-%d_%HUTC'),
                                                    impact_type="displacement",
                                                    tc_haz=tc_haz,
                                                    tc_name=tc_name,
                                                    impact=impact_displacement)

        save_forecast_summary(imp_displacement_summary, 
            SAVE_DIR +make_save_summary_filename(imp_displacement_summary))

