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
sample_file_2 = 'soilw.mon.1991-2020.ltm.v2.nc'
path_to_file = os.path.join(os.getcwd(), sample_file_2)

print(os.path.exists(path_to_file))
print('exists?')



def generate_maps_for_file(path_to_file, projection='merc'):
    previews_returned = []

    ds1 = Dataset(path_to_file)
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
            current_variable_shape = current_variable.shape
            print(type(current_variable_shape))
            shape_list = list(current_variable.shape)
            has_lat_lon_values = set(lat_lon_shape_values).issubset(shape_list)
            if has_lat_lon_values:
                variable_names_to_plot.append(variable)

    lats = ds1.variables[lat_name][:]
    lons = ds1.variables[lon_name][:]
    use_meshgrid = False
    # if the lat and lon are 1 dimensional arrays, we need to use
    # meshgrid to send in 2 dimensional arrays for matplotlib
    if len(lats.shape) == 1 and len(lons.shape) == 1:
        use_meshgrid = True

    for variable in variable_names_to_plot:
        print(variable)
        current_variable = ds1[variable]
        try:
            if current_variable.long_name:
                long_name = current_variable.long_name
        except Exception as e:
            long_name = current_variable.name
        print('before range')
        units = None
        try:
            units = current_variable.units
        except Exception as e:
            print("no units")
        non_matching_index = []
        current_variable_shape = current_variable.shape
        current_variable_shape_list = list(current_variable_shape)
        for i in range(0, len(current_variable_shape_list)):
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
                m2 = Basemap(projection=projection, llcrnrlat=-80, urcrnrlat=80,
                             llcrnrlon=-180, urcrnrlon=180, lat_ts=20, resolution='c')
                # if we need to use a meshgrid for 1 dimensional lat and lon
                if use_meshgrid:
                    gridlons, gridlats = np.meshgrid(lons, lats)
                    xi, yi = m2(gridlons, gridlats)
                else:
                    xi, yi = m2(lons, lats)

                squeezed_data = np.squeeze(current_time_variable_data)
                max = np.nanmax(squeezed_data)
                min = np.nanmin(squeezed_data)
                if min > 0:
                    min = 0
                cs2 = m2.pcolor(xi, yi, squeezed_data)
                m2.drawcoastlines()
                m2.drawcountries()
                m2.drawparallels(np.arange(-90., 91., 30.))
                m2.drawmeridians(np.arange(-180., 181., 60.))
                cbar = m2.colorbar()
                cbar.solids.set_edgecolor("face")
                cbar.set_ticks([min,max])
                title = long_name
                if units:
                    title = title + '('+str(units)+')'
                plt.title(title)

                plot_name = long_name + str(i) + '_' + str(non_matching_shape_size) + '.png'
                plt.savefig(plot_name)
                previews_returned.append(plot_name)
                plt.clf()
        # if it is NOT time series data
        if len(non_matching_index) == 0:
            m2 = Basemap(projection='merc', llcrnrlat=-80, urcrnrlat=80,
                         llcrnrlon=-180, urcrnrlon=180, lat_ts=20, resolution='c')
            # if we need to use a meshgrid for 1 dimensional lat and lon
            if use_meshgrid:
                gridlons, gridlats = np.meshgrid(lons, lats)
                xi, yi = m2(gridlons, gridlats)
            else:
                xi, yi = m2(lons, lats)
            squeezed_data = np.squeeze(variable_data)
            max = np.nanmax(squeezed_data)
            min = np.nanmin(squeezed_data)
            if min > 0:
                min = 0
            cs2 = m2.pcolor(xi, yi, squeezed_data)
            m2.drawcoastlines()
            m2.drawcountries()
            m2.drawparallels(np.arange(-90., 91., 30.))
            m2.drawmeridians(np.arange(-180., 181., 60.))
            cbar = m2.colorbar()
            cbar.solids.set_edgecolor("face")
            cbar.set_ticks([min, max])
            plot_name = long_name + '.png'
            plt.savefig(plot_name)
            previews_returned.append(plot_name)
            plt.clf()
    return previews_returned



if __name__ == "__main__":
    returned = generate_maps_for_file(path_to_file=path_to_file)
    print('done')