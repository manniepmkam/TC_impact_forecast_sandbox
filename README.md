# TC impact forecast sandbox
Scripts here produce a daily impact forecast from tropical cyclones following [Kam et al. (2024)](https://www.nature.com/articles/s41467-024-53200-w).

## Content
### Main scripts
`plot_tracks_overview_daily.py`: Python script that download the latest [ECMWF TC tracks forecast](https://www.ecmwf.int/en/forecasts/charts/latest-tropical-cyclones-forecast) and plot them into a globle map. Available as a PNG plot and an interactive map.

`tc_windfield_compute.py`: Python script that download the latest ECMWF TC tracks forecast and compute the TC wind field using the Hurricane Pressure-Wind Model. Output the TC wind field in hdf5 files.

`impact_calculate.py`: Python script that compute impacts from TC in terms of exposed population to user's defined threshold of wind speed, and displacement. Execute only after running `tc_windfield_compute.py`.

### Scripts contain useful function
1. `tc_tracks_func.py`
2. `impact_calc_func.py`
3. `plot_func.py`

## Requirements
Requires:
- Python 3.11+ environment (best to use conda for CLIMADA repository)
- *CLIMADA* repository version v5.0.0+: https://github.com/CLIMADA-project/climada_python
- *CLIMADA Petals* repository version v5.0.0+: https://github.com/CLIMADA-project/climada_petals
