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

def generate_plots(current_filename, projection="Mercator"):
    ds = Dataset(current_filename)

    variable_names = ds.variables.keys()

    lats = ds.variables['Latitude'][:]
    lons = ds.variables['Longitude'][:]

    plt.clf()
    for variable_name in variable_names:
        try:
            if 'Latitude' != variable_name and 'Longitude' != variable_name:
                current_variable_values = ds[variable_name][:]
                current_variable_data = current_variable_values.data
                # if there is more than one array (this looks like an error with the original data)
                if len(current_variable_data.shape) > 2:
                    current_variable_data = current_variable_data[0]
                    new_shape = current_variable_data.shape
                if projection == 'Mercator':
                    m2 = Basemap(projection='merc', llcrnrlat=-80, urcrnrlat=80,
                             llcrnrlon=-180, urcrnrlon=180, lat_ts=20, resolution='c')
                elif projection == 'Polar Stereographic':
                    m2 = Basemap(projection='npstere', boundinglat=10, lon_0=270, resolution='l')


                xi, yi = m2(lons, lats)
                squeezed_data = np.squeeze((current_variable_data))
                cs2 = m2.pcolor(xi, yi, np.squeeze(current_variable_data))

                m2.drawcoastlines()
                # m2.drawcountries()
                m2.drawparallels(np.arange(-90., 91., 30.))
                m2.drawmeridians(np.arange(-180., 181., 60.))

                plot_name = current_filename + '_' + variable_name + '.png'
                plt.savefig(plot_name)
                plt.clf()
        except Exception as e:
            print("Error with variable", variable_name)

generate_plots(current_filename=sample_file)