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
# sample_file = 'pr_2020.nc'
def main():
    print('doing files')
    ds = Dataset(sample_file)
    variable_names = list(ds.variables.keys())


    lats = ds.variables['Latitude'][:]
    lons = ds.variables['Longitude'][:]
    sample_variable = 'Cloud_Optical_Thickness_Combined_Mean'



    if sample_variable in variable_names:
        current_variable = ds.variables[sample_variable]

    current_variable_values = current_variable[:]
    current_variable_data = current_variable_values.data

    lon_0 = lons.mean()
    lat_0 = lats.mean()

    # m = Basemap(width=5000000, height=3500000,
    #             resolution='l', projection='stere',
    #             lat_ts=40, lat_0=lat_0, lon_0=lon_0)

    # Mercator projection Basemap
    # m2 = Basemap(projection='merc', llcrnrlat=-80, urcrnrlat=80,
    #             llcrnrlon=-180, urcrnrlon=180, lat_ts=20, resolution='c')

    # polar stereographic projection basemap

    m2 = Basemap(projection='npstere', boundinglat=10, lon_0=270, resolution='l')
    xi, yi = m2(lons, lats)



    cs2 = m2.pcolor(xi, yi, np.squeeze(current_variable_data))

    m2.drawcoastlines()
    m2.drawcountries()
    m2.drawparallels(np.arange(-90., 91., 30.))
    m2.drawmeridians(np.arange(-180., 181., 60.))
    plt.savefig('polar.png')
    # plt.show()

    # Add Colorbar
    print('here')

if __name__ == "__main__":
    main()