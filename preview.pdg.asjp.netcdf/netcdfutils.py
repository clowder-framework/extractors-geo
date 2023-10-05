import os
import netCDF4 as nc
import sys
from netCDF4 import Dataset as Dataset
import matplotlib.pyplot as plt
import numpy as np
import mpl_toolkits
from mpl_toolkits.basemap import Basemap
plt.rcParams['figure.figsize'] = (16.0, 12.0)


sample_file = '../preview.netcdf/ASJP_Year_2023_Day_218.nc4'
sample_file = '../preview.netcdf/soilw.mon.1981-2010.ltm.v2.nc'


def process_file(filename):
    ds = Dataset(sample_file)

    dimension_keys = ds.dimensions.keys()
    # TODO is this lat lon, or lat lon and time

    dimensions_lat = False
    dimensions_lon = False
    dimensions_time = False
    dimension_day = False
    time_variable = ""
    for dim in dimension_keys:
        dim_name = str(dim).lower()
        if 'lat' in str(dim).lower():
            dimensions_lat = True
        if 'lon' in str(dim).lower():
            dimensions_lon = True
        if 'time' in str(dim).lower():
            dimensions_time = True
            time_variable = dim
        if 'day' in str(dim).lower():
            dimension_day = True
            time_variable = dim

    variable_names = list(ds.variables.keys())

    lat_name = ""
    lon_name = ""
    for variable in variable_names:
        lowercase_variable = str(variable).lower()
        if 'lat' in lowercase_variable:
            lat_name = variable
        if 'lon' in lowercase_variable:
            lon_name = variable

    for variable in variable_names:
        lowercase_variable = str(variable).lower()
        is_lat_lon_or_time = 'lat' in lowercase_variable or 'lon' in lowercase_variable or (lowercase_variable == 'time' or lowercase_variable == 'day')
        if not is_lat_lon_or_time:
            try:
                generate_mercator_plot_for_variable(current_dataset=ds, lat=lat_name, lon=lon_name, current_variable=variable, current_filename=sample_file, time=time_variable)
            except Exception as e:
                print(e)

if __name__ == "__main__":
    main()