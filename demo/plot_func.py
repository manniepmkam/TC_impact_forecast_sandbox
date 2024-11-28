import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm_mp
from mpl_toolkits.axes_grid1 import make_axes_locatable
import cartopy.crs as ccrs
import cartopy.feature as cf   
from matplotlib.collections import LineCollection
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D

from climada.hazard import TCTracks
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

def plot_global_tracks(tc_tracks: TCTracks, figsize=(15,8)):

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

def plot_empty_base_map():
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