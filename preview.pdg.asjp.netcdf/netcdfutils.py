import os
import netCDF4 as nc
import sys
from netCDF4 import Dataset as Dataset
import matplotlib.pyplot as plt
import numpy as np
import mpl_toolkits
from mpl_toolkits.basemap import Basemap
plt.rcParams['figure.figsize'] = (16.0, 12.0)


sample_file = 'ASJP_Year_2023_Day_218.nc4'
sample_file = 'soilw.mon.1981-2010.ltm.v2.nc'

def generate_mercator_plot_for_variable(current_dataset, lat, lon, current_variable, current_filename, time=""):
    lats = current_dataset.variables[lat][:]
    lons = current_dataset.variables[lon][:]

    current_variable_values = current_dataset[current_variable][:]
    current_variable_data = current_variable_values.data

    current_variable_shape = current_variable_data.shape
    time_index = None
    if time == 'time'or time == 'day' or time == 'days':
        print('this is something else')
        print('this is data organized by day')
    for i in range(0, len(current_variable_shape)):
        if current_variable_shape[i] == 366 or current_variable_shape[i] == 365:
            time_index = i
            total_days = current_variable_shape[i]
    # mercator projection basemap by default
    if time_index is not None and (total_days == 366 or total_days == 365):
        print('we have a time index')
        print('if we have 366 days a year we will take a day')

        print('we make 4 maps, day 0, day 90, day 180, day 270 and day 360')
        days_to_map = [0, 90, 180, 270, 360]
        for current_day in days_to_map:
            current_day_data = current_variable_data[current_day]
            print('got data')
            m2 = Basemap(projection='merc', llcrnrlat=-80, urcrnrlat=80,
                         llcrnrlon=-180, urcrnrlon=180, lat_ts=20, resolution='c')

            if len(lons) > 1:
                current_lon = lons[0]
            else:
                current_lon = lons
            if len(lons) > 1:
                current_lat = lats[0]
            else:
                current_lat = lats
            xi, yi = m2(current_lon, current_lat)

            cs2 = m2.pcolor(xi, yi, np.squeeze(current_day_data))
            m2.drawcoastlines()
            m2.drawcountries()
            m2.drawparallels(np.arange(-90., 91., 30.))
            m2.drawmeridians(np.arange(-180., 181., 60.))

            plot_name = current_filename + '_' + current_variable + '.png'
            plt.savefig(plot_name)
            plt.clf()
    else:
        m2 = Basemap(projection='merc', llcrnrlat=-80, urcrnrlat=80,
                     llcrnrlon=-180, urcrnrlon=180, lat_ts=20, resolution='c')

        xi, yi = m2(lons, lats)

        cs2 = m2.pcolor(xi, yi, np.squeeze(current_variable_data))

        m2.drawcoastlines()
        m2.drawcountries()
        m2.drawparallels(np.arange(-90., 91., 30.))
        m2.drawmeridians(np.arange(-180., 181., 60.))

        plot_name = current_filename + '_' + current_variable + '.png'
        plt.savefig(plot_name)
        plt.clf()


def main():
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