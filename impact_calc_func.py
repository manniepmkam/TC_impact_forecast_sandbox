#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 11:35:50 2024

Useful functions for impact calculations.

@author: Pui Man (Mannie) Kam
"""
import numpy as np
import pandas as pd
import json
from typing import Union
from pathlib import Path

from climada.hazard import TCTracks
from climada.entity import ImpactFunc, ImpfTropCyclone, ImpactFuncSet
from climada.engine import Impact

#  List of regions and the countries
iso3_to_basin = {'NA1': ['AIA', 'ATG', 'ARG', 'ABW', 'BHS', 'BRB', 'BLZ', 'BMU',
                 'BOL', 'CPV', 'CYM', 'CHL', 'COL', 'CRI', 'CUB', 'DMA',
                 'DOM', 'ECU', 'SLV', 'FLK', 'GUF', 'GRD', 'GLP', 'GTM',
                 'GUY', 'HTI', 'HND', 'JAM', 'MTQ', 'MEX', 'MSR', 'NIC',
                 'PAN', 'PRY', 'PER', 'PRI', 'SHN', 'KNA', 'LCA', 'VCT',
                 'SXM', 'SUR', 'TTO', 'TCA', 'URY', 'VEN', 'VGB', 'VIR'],
                'NA2': ['CAN', 'USA'],
                'NI': ['AFG', 'ARM', 'AZE', 'BHR', 'BGD', 'BTN', 'DJI', 'ERI',
                        'ETH', 'GEO', 'IND', 'IRN', 'IRQ', 'ISR', 'JOR', 'KAZ',
                        'KWT', 'KGZ', 'LBN', 'MDV', 'MNG', 'MMR', 'NPL', 'OMN',
                        'PAK', 'QAT', 'SAU', 'SOM', 'LKA', 'SYR', 'TJK', 'TKM',
                        'UGA', 'ARE', 'UZB', 'YEM'],
                'OC1': ['ASM', 'COK', 'FJI', 'PYF', 'GUM', 'KIR', 'MHL', 'FSM', 
                            'NRU', 'NCL', 'NIU', 'NFK', 'MNP', 'PLW', 'PNG', 'PCN', 
                            'WSM', 'SLB', 'TLS', 'TKL', 'TON', 'TUV', 'VUT', 'WLF'],
                'OC2': ['AUS', 'NZL'],
                'SI': ['COM', 'COD', 'SWZ', 'MDG', 'MWI', 'MLI', 'MUS', 'MOZ',
                        'ZAF', 'TZA', 'ZWE'],
                'WP1': ['KHM', 'IDN', 'LAO', 'MYS', 'THA', 'VNM'],
                'WP2': ['PHL'],
                'WP3': ['CHN'],
                'WP4': ['HKG', 'JPN', 'KOR', 'MAC', 'TWN'],
                'ROW': ['ALB', 'DZA', 'AND', 'AGO', 'ATA', 'AUT', 'BLR', 'BEL',
                        'BEN', 'BES', 'BIH', 'BWA', 'BVT', 'BRA', 'IOT', 'BRN',
                        'BGR', 'BFA', 'BDI', 'CMR', 'CAF', 'TCD', 'CXR', 'CCK',
                        'COG', 'HRV', 'CUW', 'CYP', 'CZE', 'CIV', 'DNK', 'EGY',
                        'GNQ', 'EST', 'FRO', 'FIN', 'FRA', 'ATF', 'GAB', 'GMB',
                        'DEU', 'GHA', 'GIB', 'GRC', 'GRL', 'GGY', 'GIN', 'GNB',
                        'HMD', 'VAT', 'HUN', 'ISL', 'IRL', 'IMN', 'ITA', 'JEY',
                        'KEN', 'PRK', 'XKX', 'LVA', 'LSO', 'LBR', 'LBY', 'LIE',
                        'LTU', 'LUX', 'MLT', 'MRT', 'MYT', 'MDA', 'MCO', 'MNE',
                        'MAR', 'NAM', 'NLD', 'NER', 'NGA', 'MKD', 'NOR', 'PSE',
                        'POL', 'PRT', 'ROU', 'RUS', 'RWA', 'REU', 'BLM', 'MAF',
                        'SPM', 'SMR', 'STP', 'SEN', 'SRB', 'SYC', 'SLE', 'SGP',
                        'SVK', 'SVN', 'SGS', 'SSD', 'ESP', 'SDN', 'SJM', 'SWE',
                        'CHE', 'TGO', 'TUN', 'TUR', 'UKR', 'GBR', 'UMI', 'ESH',
                        'ZMB', 'ALA']}

# RMSF optimised v_half for each region
v_half_per_region = {'NA1': 51.6,
                    'NA2': 84.1,
                    'NI': 41.3,
                    'OC1': 44.3,
                    'OC2': 47.4,
                    'SI': 40.8,
                    'WP1': 42.2,
                    'WP2': 46.7,
                    'WP3': 35.7,
                    'WP4': 93.1,
                    'ROW': 49.5}

def impf_set_exposed_pop(threshold: np.float64 = 32.92):
    """
    Impact function set that estimate the number of people exposed 
    to a threshold of windspeed.
    
    Parameters
    ----------
    threshold : np.float64
        Wind speed threshold that people are exposed to.
        Default: 32.92 (Hurrane Cat. 1)

    Returns
    -------
    impf_set : climada.entity.ImpactDuncSet
        Impact function set that contains a step impact function.
    """

    impf = ImpactFunc.from_step_impf((0,threshold, 100),
                                     haz_type="TC")
    
    impf_set = ImpactFuncSet()
    impf_set.append(impf)

    return(impf_set)

def impf_set_displacement(country: str):
    """
    Impact function set that estimate the number of displacement. The shape of the
    impact function depends on the countries and their respective region. 
    Details see Kam et al. (2024).

    Parameters
    ----------
    country : str
        Single country in ISO3 alpha.

    Returns
    -------
    impf_set : climada.entity.ImpactDuncSet
        Impact function set that contains a displacement impact function.
    """

    v_half = get_impf_v_half(country)

    impf = ImpfTropCyclone.from_emanuel_usa(v_half=v_half)

    impf_set = ImpactFuncSet()
    impf_set.append(impf)

    return(impf_set)


def get_impf_v_half(country: str):
    """
    Get the impact function parameter v_half according to selected country (country_iso3).

    Parameters
    ----------
        country: str
            Single country in ISO3 alpha.

    Returns
    -------
    v_half : np.float64
        The impact function parameter v_half for the respective country.
    """
    # Get basin in which country_iso3 lies
    basin = [key
            for key, list_of_values in iso3_to_basin.items()
            if country in list_of_values]
    
    # Get impf_distr corresponding to basin
    v_half = v_half_per_region[basin[0]]
    
    return v_half

def round_to_previous_12h_utc(timestamp: pd.Timestamp):
    """
    Rounding the time into 00 or 12 UTC
    """
    # Ensure the timestamp is in UTC
    if timestamp.tz is None:
        utc_timestamp = timestamp.tz_localize('UTC')
    else:
        utc_timestamp = timestamp.tz_convert('UTC')
    
    # Round down to the nearest hour
    rounded = utc_timestamp.floor('H')
    
    # Determine the previous 12-hour mark
    if rounded.hour < 12:
        return rounded.replace(hour=0)
    else:
        return rounded.replace(hour=12)
    
def summarize_forecast(country_iso3: str,
                       forecast_time: str,
                       impact_type: str,
                       tc_haz: TCTracks,
                       tc_name: str,
                       impact: Impact):
    """
    Summarizing forecast into a dictionary
    """
    # check impact event length
    ## incase the TC ensemble number is less than 51
    # get the array for each event
    imp_at_event = _check_event_no(impact)

    imp_summary_dict={
        "countryISO3": country_iso3,
        "hazardType": impact.haz_type,
        "impactType": impact_type,
        "initializationTime": forecast_time,
        "eventName": tc_name,
        "mean": np.mean(imp_at_event),
        "median": np.median(imp_at_event),
        "05perc": np.percentile(imp_at_event, 5),
        "25perc": np.percentile(imp_at_event, 25),
        "75perc": np.percentile(imp_at_event, 75),
        "95perc": np.percentile(imp_at_event, 95),
        "weatherModel": "ECMWF",
        "impactUnit": "people"
    }
    return imp_summary_dict

def save_forecast_summary(forecast_summary: dict,
                          save_dir: Union[str, Path]):
    """
    Save the  summary into a geoJSON feature collection.
    """
    # Create a GeoJSON FeatureCollection structure
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": forecast_summary,
                "geometry": None  # Set to None if there's no specific geometry
            }
        ]
    }

    # Save the GeoJSON data to a file
    with open(save_dir, 'w') as f:
        json.dump(geojson_data, f, indent=4)

def make_save_summary_filename(imp_summary_dict: dict):
    """
    Make a file name for saving
    """
    forecast_filename = (
        f'impact-summary_TC_ECMWF_ens_{imp_summary_dict["eventName"]}_{imp_summary_dict["initializationTime"]}'
        f'_{imp_summary_dict["countryISO3"]}_{imp_summary_dict["impactType"]}.json'
        )
    return forecast_filename

def _check_event_no(impact: Impact):
    """
    For some TC events, there is less than 51 esemble. Hence, checke if the 
    impact.at_event lenth equals to 51. If not, fill the missing event as 0.
    """

    imp_at_event = impact.at_event

    if len(imp_at_event) == 51:
        return imp_at_event
    else:
        no_missing_zeros = 51 - len(imp_at_event)
        new_imp_at_event = np.pad(imp_at_event, pad_width=(0, no_missing_zeros),
                                  mode='constant', constant_values=0)
        return new_imp_at_event
