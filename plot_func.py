#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Useful functions for plotting.

@author: Pui Man (Mannie) Kam
"""

import numpy as np
import pandas as pd
from typing import Union
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cm as cm_mp
from matplotlib.collections import LineCollection
from matplotlib.colors import BoundaryNorm, ListedColormap, Normalize
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1 import make_axes_locatable
import cartopy.crs as ccrs
import cartopy.feature as cf
import contextily as ctx
import plotly.graph_objects as go

from climada.hazard import TCTracks
from climada.engine import Impact
import climada.util.coordinates as u_coord

SAFFIR_SIM_CAT = [17.49, 32.92, 42.7, 49.39, 58.13, 70.48, 1000]

CAT_NAMES = {
    -1: "Tropical Depression",
    0: "Tropical Storm",
    1: "Hurricane Cat. 1",
    2: "Hurricane Cat. 2",
    3: "Hurricane Cat. 3",
    4: "Hurricane Cat. 4",
    5: "Hurricane Cat. 5",
}
"""Saffir-Simpson category names."""

CAT_COLORS = cm_mp.rainbow(np.linspace(0, 1, len(SAFFIR_SIM_CAT)))
"""Color scale to plot the Saffir-Simpson scale."""

CUSTOM_LEGEND = ["Tropical Depression", "Tropical Storm", 
                 "Hurricane Cat. 1", "Hurricane Cat. 2", "Hurricane Cat. 3",
                 "Hurricane Cat. 4", "Hurricane Cat. 5"]

cmap = ListedColormap(colors=CAT_COLORS)
cmap_hex = []
for i in range(cmap.N):
    rgba = cmap(i)
    # rgb2hex accepts rgb or rgba
    cmap_hex.append(mpl.colors.rgb2hex(rgba))

def categorize_wind(speed):
    """Saffir-Simpson Hurricane Scale"""
    if speed < 17.49:
        return -1  # Tropical depression
    elif speed < 32.92:
        return 0  # Tropical storm
    elif speed < 42.7:
        return 1  # Category 1
    elif speed < 49.39:
        return 2  # Category 2
    elif speed < 58.13:
        return 3  # Category 3
    elif speed < 70.48:
        return 4  # Category 4
    elif speed < 1000:
        return 5  # Category 5
    else:
        return 999

def plot_global_tracks(tc_tracks: TCTracks, figsize=(15,8)):
    """Plot the global forecast TC tracks"""
    # define the figure and figure extent
    fig = plt.figure(figsize=figsize)
    axis = plt.axes(projection=ccrs.PlateCarree())
    axis.add_feature(cf.COASTLINE, color='k',lw=.5)
    axis.add_feature(cf.BORDERS, color="k", lw=.3)
    axis.add_feature(cf.LAND, facecolor="rosybrown", alpha=.2)
    axis.set_extent([-180, 180, -80, 80], crs=ccrs.PlateCarree())

    # grid lines on the lat lon
    gl = axis.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                  linewidth=.5, color='gray', alpha = 0.25,
                  linestyle='--')
    # labels on bottom and left axes
    axis.xlabels_top = False
    axis.ylabels_right = False

    # plot the tracks
    synth_flag = False
    cmap = ListedColormap(colors=CAT_COLORS)
    norm = BoundaryNorm([0] + SAFFIR_SIM_CAT, len(SAFFIR_SIM_CAT))

    for track in tc_tracks.data:
    #    track.lon.values[np.where(track.lon.values<0)] +=360
        lonlat = np.stack([track.lon.values, track.lat.values], axis=-1)
        lonlat[:, 0] = u_coord.lon_normalize(lonlat[:, 0])
        segments = np.stack([lonlat[:-1], lonlat[1:]], axis=1)
        # remove segments which cross 180 degree longitude boundary
        segments = segments[segments[:, 0, 0] * segments[:, 1, 0] >= 0, :, :]
        track_lc = LineCollection(segments, cmap=cmap, norm=norm,
                                    linestyle='-', lw=.7)
        track_lc.set_array(track.max_sustained_wind.values)
        axis.add_collection(track_lc)

    leg_lines = [Line2D([0], [0], color=CAT_COLORS[i_col], lw=2)
                for i_col in range(len(SAFFIR_SIM_CAT))]
    leg_names = [CAT_NAMES[i_col] for i_col in sorted(CAT_NAMES.keys())]
    axis.legend(leg_lines, leg_names, loc=3, fontsize=12)

    plt.tight_layout()

    return axis

def plot_empty_base_map(figsize=(15,8)):
    """Empty base map if no active storm"""
    # define the figure and figure extent
    fig = plt.figure(figsize=figsize)
    axis = plt.axes(projection=ccrs.PlateCarree())
    axis.add_feature(cf.COASTLINE, color='k',lw=.5)
    axis.add_feature(cf.BORDERS, color="k", lw=.3)
    axis.add_feature(cf.LAND, facecolor="rosybrown", alpha=.2)
    axis.set_extent([-180, 180, -80, 80], crs=ccrs.PlateCarree())

    # grid lines on the lat lon
    gl = axis.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                  linewidth=.5, color='gray', alpha = 0.25,
                  linestyle='--')
    # labels on bottom and left axes
    axis.xlabels_top = False
    axis.ylabels_right = False

    leg_lines = [Line2D([0], [0], color=CAT_COLORS[i_col], lw=2)
                for i_col in range(len(SAFFIR_SIM_CAT))]
    leg_names = [CAT_NAMES[i_col] for i_col in sorted(CAT_NAMES.keys())]
    axis.legend(leg_lines, leg_names, loc=3, fontsize=12)

    plt.tight_layout()

    return axis

def plot_interactive_map(tc_tracks: TCTracks, figsize=(15,8)):
    """Interactive map for global forecast TC tracks"""
    fig = go.Figure()

    for track in tc_tracks.data:
        df = pd.DataFrame({
            'lon': track['lon'],
            'lat': track['lat'],
            'wind_speed': track['max_sustained_wind'],
            'category': [categorize_wind(ws) for ws in track['max_sustained_wind']]
        })

        for i in range(len(df) - 1):
            fig.add_trace(go.Scattergeo(
                lon = df['lon'][i:i+2],
                lat = df['lat'][i:i+2],
                mode = 'lines',
                line = dict(width = 2, color = cmap_hex[df['category'][i]+1]),
                name = f"{track.name} - Cat {df['category'][i]}",
                showlegend = False
            ))

    # Add invisible traces for legend
    for category, color in zip(CUSTOM_LEGEND, cmap_hex):
        fig.add_trace(go.Scattergeo(
            lon = [None],
            lat = [None],
            mode = 'lines',
            line = dict(width = 2, color = color),
            name = category,
            showlegend = True
        ))

    fig.update_layout(
        title = 'Tropical Cyclone Tracks',
        geo = dict(
            showland = True,
            showcountries = True,
            showocean = True,
            countrywidth = 0.5,
            landcolor = 'rgb(241, 232, 232)',
            oceancolor = 'rgb(255, 255, 255)',
            projection = dict(type = 'natural earth')
        ),
        legend_title = 'Saffir–Simpson Scale',
        legend = dict(
            yanchor = "top",
            y = 1,
            xanchor = "left",
            x = .95
        )
    )
    return fig

def plot_empty_interactive_map(figsize=(15,8)):
    """Empty base map if no active storm"""
    fig = go.Figure()
    # Add invisible traces for legend
    for category, color in zip(CUSTOM_LEGEND, cmap_hex):
        fig.add_trace(go.Scattergeo(
            lon = [None],
            lat = [None],
            mode = 'lines',
            line = dict(width = 2, color = color),
            name = category,
            showlegend = True
        ))

    fig.update_layout(
        title = 'Tropical Cyclone Tracks',
        geo = dict(
            showland = True,
            showcountries = True,
            showocean = True,
            countrywidth = 0.5,
            landcolor = 'rgb(241, 232, 232)',
            oceancolor = 'rgb(255, 255, 255)',
            projection = dict(type = 'natural earth')
        ),
        legend_title = 'Saffir–Simpson Scale',
        legend = dict(
            yanchor = "top",
            y = 1,
            xanchor = "left",
            x = .95
        )
    )
    return 
def make_save_map_file_name(imp_summary_dict: dict):
    """
    Make a file name for saving

    Parameters
    ----------
    imp_summary_dict: dict
        Impact forecast summary
    
    Returns
    -------
    forecast_filename: str
        File name for saving the files
    """
    forecast_filename = (
        f'impact-map_TC_ECMWF_ens_{imp_summary_dict["eventName"]}_{imp_summary_dict["initializationTime"]}'
        f'_{imp_summary_dict["countryISO3"]}_{imp_summary_dict["impactType"]}.png'
        )
    return forecast_filename

def make_save_histogram_file_name(imp_summary_dict: dict):
    """
    Make a file name for saving

    Parameters
    ----------
    imp_summary_dict: dict
        Impact forecast summary
    
    Returns
    -------
    forecast_filename: str
        File name for saving the files
    """
    forecast_filename = (
        f'impact-histogram_TC_ECMWF_ens_{imp_summary_dict["eventName"]}_{imp_summary_dict["initializationTime"]}'
        f'_{imp_summary_dict["countryISO3"]}_{imp_summary_dict["impactType"]}.png'
        )
    return forecast_filename

def plot_imp_map_exposed(impact_summary_dict: dict,
                         impact: Impact):
    """Plot the ensemble average map for exposed population"""

    impact_exp = impact._build_exp()

    extent = impact_exp.gdf.geometry.to_crs(epsg=3857).total_bounds
    impact_exp.to_crs("EPSG:3857", inplace=True)
    gdf = impact_exp.gdf

    cmap = plt.get_cmap("YlOrBr")
    n = 256  # Number of discrete colors in the colormap
    vals = cmap(np.linspace(0, 1, n))
    vals[:, -1] = np.linspace(0.0, 1.0, n)  # Gradual transparency

    # Make values below 10 transparent
    threshold = 10
    alphas = np.ones(n)
    alphas[:int(threshold / np.max(gdf["value"]) * n)] = 0.0
    vals[:, -1] = alphas

    transparent_cmap = ListedColormap(vals)

    fig, ax = plt.subplots()

    vmax = np.max(gdf["value"])
    vmin = threshold  # Start normalization from threshold

    norm = Normalize(vmin=vmin, vmax=vmax)

    hb = ax.hexbin(
        x=gdf.geometry.x,
        y=gdf.geometry.y,
        C=gdf["value"],
        reduce_C_function=np.sum,
        norm=norm,
        gridsize=200,
        extent=(extent[0], extent[2], extent[1], extent[3]),
        lw=0.0,
        cmap=transparent_cmap,
    )

    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)

    plt.colorbar(hb, ax=ax, label="Ensemble Avg. Exposed People", extend='min')

    # Main title
    ax.set_title(
    f'Forecasted Exposed Population in {impact_summary_dict["countryISO3"]}\nby TC {impact_summary_dict["eventName"]}'
    )

    # get information for the title
    mean = int(np.mean(impact.at_event))
    std = int(np.std(impact.at_event))

    # box with information
    ax.text(
        0.03,
        0.03,
        f'Forecast Date: {impact_summary_dict["initializationTime"]}\nEstimated Exposed Population: {mean:,}±{std:,}',
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        bbox={"boxstyle": "round", "facecolor": "white"},
        zorder=10,
    )

    return ax

def plot_imp_map_displacement(impact_summary_dict: dict,
                              impact: Impact):
    """Plot the ensemble average map for displacement"""

    impact_exp = impact._build_exp()

    extent = impact_exp.gdf.geometry.to_crs(epsg=3857).total_bounds
    impact_exp.to_crs("EPSG:3857", inplace=True)
    gdf = impact_exp.gdf

    cmap = plt.get_cmap("YlOrBr")
    n = 256  # Number of discrete colors in the colormap
    vals = cmap(np.linspace(0, 1, n))
    vals[:, -1] = np.linspace(0.0, 1.0, n)  # Gradual transparency

    # Make values below 10 transparent
    threshold = 10
    alphas = np.ones(n)
    alphas[:int(threshold / np.max(gdf["value"]) * n)] = 0.0
    vals[:, -1] = alphas

    transparent_cmap = ListedColormap(vals)

    fig, ax = plt.subplots()

    vmax = np.max(gdf["value"])
    vmin = threshold  # Start normalization from threshold

    norm = Normalize(vmin=vmin, vmax=vmax)

    hb = ax.hexbin(
        x=gdf.geometry.x,
        y=gdf.geometry.y,
        C=gdf["value"],
        reduce_C_function=np.sum,
        norm=norm,
        gridsize=200,
        extent=(extent[0], extent[2], extent[1], extent[3]),
        lw=0.0,
        cmap=transparent_cmap,
    )

    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

    ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)

    plt.colorbar(hb, ax=ax, label="Ensemble Avg. Displacement", extend='min')

    # Main title
    ax.set_title(
    f'Forecasted Displacement in {impact_summary_dict["countryISO3"]}\nby TC {impact_summary_dict["eventName"]}'
    )

    # get information for the title
    mean = int(np.mean(impact.at_event))
    std = int(np.std(impact.at_event))

    # box with information
    ax.text(
        0.03,
        0.03,
        f'Forecast Date: {impact_summary_dict["initializationTime"]}\nEstimated Displacement: {mean:,}±{std:,}',
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        bbox={"boxstyle": "round", "facecolor": "white"},
        zorder=10,
    )

    return ax

def plot_histogram(impact_summary_dict: dict,
                    impact: Impact):
    
    """plot the histogram"""
    num_bins = 40
    data_range = impact.at_event.max() - impact.at_event.min()
    bin_width = data_range / num_bins

    # Calculate adaptive bins based on the data range
    bins = np.arange(impact.at_event.min(), 
                     impact.at_event.max() + bin_width, 
                     bin_width)
    
    # Calculate histogram values and normalize them to probabilities
    hist_values, bin_edges = np.histogram(impact.at_event, bins=bins)
    bin_probabilities = hist_values / hist_values.sum() *100  # Normalize to probabilities
    
    fig, ax = plt.subplots(1,1,figsize=(6,4))

    # Plot the histogram
    plt.bar(bin_edges[:-1], bin_probabilities, width=bin_width, color='lightsteelblue', alpha=1, edgecolor='w', align='edge')
    plt.grid(visible=True)

    plt.xlabel('Forecasted impact (people)', fontsize=10)
    plt.ylabel('Probability (%)', fontsize=10)

    plt.figtext(0.13,0.95, f'TC {impact_summary_dict["eventName"]} in {impact_summary_dict["countryISO3"]}',
            color='k', fontsize=12, ha='left')
    plt.figtext(0.13,0.9, impact_summary_dict["impactType"],
            color='k', fontsize=10, ha='left')
    plt.figtext(0.9,0.95,
                impact_summary_dict["initializationTime"],
                color='red', fontsize=10, ha='right')
    plt.figtext(0.9,0.9,
                f'Mean: {int(np.mean(impact.at_event))}',
                color='k', fontsize=10, ha='right')
    
    spines = ["top","right","left","bottom"]
    for s in spines:
        ax.spines[s].set_visible(False)

    return ax