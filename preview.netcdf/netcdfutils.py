import os
import netCDF4 as nc
import sys
from netCDF4 import Dataset as Dataset
import matplotlib.pyplot as plt
import numpy as np
import mpl_toolkits
from mpl_toolkits.basemap import Basemap
plt.rcParams['figure.figsize'] = (16.0, 12.0)


sample_file = 'ASJP_Year_2023_Day_217.nc4'

def generate_mercator_plot_for_variable(current_dataset, current_variable, current_filename):
    lats = current_dataset.variables['Latitude'][:]
    lons = current_dataset.variables['Longitude'][:]

    current_variable_values = current_dataset[current_variable][:]
    current_variable_data = current_variable_values.data

    # mercator projection basemap by default
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


# sample_file = 'pr_2020.nc'
def main():
    ds = Dataset(sample_file)
    variable_names = list(ds.variables.keys())

    for variable in variable_names:
        if variable != 'Latitude' and variable != 'Longitude':
            try:
                generate_mercator_plot_for_variable(current_dataset=ds, current_variable=variable, current_filename=sample_file)
            except Exception as e:
                print(e)

if __name__ == "__main__":
    main()