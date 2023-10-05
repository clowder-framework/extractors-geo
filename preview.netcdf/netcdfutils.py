import os
import netCDF4 as nc
import sys
from netCDF4 import Dataset as Dataset
import matplotlib.pyplot as plt
import numpy as np
import mpl_toolkits
from mpl_toolkits.basemap import Basemap
plt.rcParams['figure.figsize'] = (16.0, 12.0)


sample_file_1 = 'ASJP_Year_2023_Day_218.nc4'
sample_file_2 = 'soilw.mon.1991-2010.ltm.v2.nc'

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
            gridlons, gridlats = np.meshgrid(lons, lats)
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

        gridlons, gridlats = np.meshgrid(lons, lats)
        xi, yi = m2(gridlons, gridlats)

        zero_data = current_variable_data[0]

        cs2 = m2.pcolor(xi, yi, np.squeeze(current_variable_data))

        m2.drawcoastlines()
        m2.drawcountries()
        m2.drawparallels(np.arange(-90., 91., 30.))
        m2.drawmeridians(np.arange(-180., 181., 60.))

        plot_name = current_filename + '_' + current_variable + '.png'
        plt.savefig(plot_name)
        plt.clf()


def main():
    current_path = os.getcwd()
    path_to_file = os.path.join(current_path, 'soilw.mon.1991-2020.ltm.v2.nc')
    print(os.path.exists(path_to_file))
    ds1 = Dataset(path_to_file)
    print(ds1)
    ds1_variables = ds1.variables

    variable_names = list(ds1.variables.keys())

    lat_name = ""
    lon_name = ""
    for variable in variable_names:
        lowercase_variable = str(variable).lower()
        if 'lat' in lowercase_variable:
            lat_name = variable
        if 'lon' in lowercase_variable:
            lon_name = variable

    # we now have the variable names, we need
    # TODO we are explicitly plotting here

    latitutde = ds1.variables[lat_name]
    longitude = ds1.variables[lon_name]
    latitude_shape = latitutde.shape
    longitude_shape = longitude.shape
    lat_lon_shape_values = []
    for shape in latitude_shape:
        lat_lon_shape_values.append(shape)
    for shape in longitude_shape:
        lat_lon_shape_values.append(shape)
    variable_names_to_plot = []
    for variable in variable_names:
        if variable != lat_name and variable != lon_name:
            current_variable = ds1[variable]
            shape_list = list(current_variable.shape)
            has_lat_lon_values = set(lat_lon_shape_values).issubset(shape_list)
            if has_lat_lon_values:
                variable_names_to_plot.append(variable)

    lats = ds1.variables[lat_name][:]
    lons = ds1.variables[lon_name][:]
    use_meshgrid = False
    if len(lats.shape) == 1 and len(lons.shape) == 1:
        use_meshgrid = True

    for variable in variable_names_to_plot:
        print(variable)
        current_variable = ds1[variable]
        non_matching_index = []
        for i in range(0, len(current_variable.shape)):
            if current_variable.shape[i] not in lat_lon_shape_values:
                non_matching_index.append(i)
        variable_data = current_variable[:]
        if len(non_matching_index) == 1:
            non_matching_shape_size = current_variable.shape[non_matching_index[0]]
            quarter_time = int(np.floor(non_matching_shape_size / 4))
            # with time series data, we will show quarterly previews

            for i in range(0,4):
                current_time_to_plot = int(np.floor(i*quarter_time))
                current_time_variable_data = variable_data[current_time_to_plot]
                print('plot this')
                m2 = Basemap(projection='merc', llcrnrlat=-80, urcrnrlat=80,
                             llcrnrlon=-180, urcrnrlon=180, lat_ts=20, resolution='c')
                # if we need to use a meshgrid for 1 dimensional lat and lon
                if use_meshgrid:
                    gridlons, gridlats = np.meshgrid(lons, lats)
                    xi, yi = m2(gridlons, gridlats)
                else:
                    xi, yi = m2(lons, lats)

                squeezed_data = np.squeeze(current_time_variable_data)
                cs2 = m2.pcolor(xi, yi, squeezed_data)
                m2.drawcoastlines()
                m2.drawcountries()
                m2.drawparallels(np.arange(-90., 91., 30.))
                m2.drawmeridians(np.arange(-180., 181., 60.))

                plot_name = 'test_' + str(i) + '.png'
                plt.savefig(plot_name)
                plt.clf()
        # if it is NOT time series data
        if len(non_matching_index) == 0:
            print('data matches')


if __name__ == "__main__":
    main()