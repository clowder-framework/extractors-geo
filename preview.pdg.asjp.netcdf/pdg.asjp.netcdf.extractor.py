#!/usr/bin/env python

"""Example extractor based on the clowder code."""

import logging
import subprocess
import pyclowder
from pyclowder.extractors import Extractor
import pyclowder.files
import os
import netCDF4 as nc
import sys
from netCDF4 import Dataset as Dataset
import matplotlib.pyplot as plt
import numpy as np
import mpl_toolkits
from mpl_toolkits.basemap import Basemap
plt.rcParams['figure.figsize'] = (16.0, 12.0)


# sample_file = 'ASJP_Year_2023_Day_218.nc4'

# setup logging for the exctractor
logging.getLogger('pyclowder').setLevel(logging.DEBUG)
logging.getLogger('__main__').setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_plots(current_filepath, current_filename, projection="Mercator"):
    ds = Dataset(current_filepath)

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
                logger.debug(f"Creating plot for variable {variable_name}")
                if projection == 'Mercator':
                    m2 = Basemap(projection='merc', llcrnrlat=-80, urcrnrlat=80,
                             llcrnrlon=-180, urcrnrlon=180, lat_ts=20, resolution='c')
                elif projection == 'Polar Stereographic':
                    m2 = Basemap(projection='npstere', boundinglat=10, lon_0=270, resolution='l')


                xi, yi = m2(lons, lats)
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


class PDG_ASJP_NetCDF(Extractor):
    """Count the number of characters, words and lines in a text file."""
    def __init__(self):
        Extractor.__init__(self)

        # add any additional arguments to parser
        # self.parser.add_argument('--max', '-m', type=int, nargs='?', default=-1,
        #                          help='maximum number (default=-1)')

        # parse command line and load default logging configuration
        self.setup()

    def process_message(self, connector, host, secret_key, resource, parameters):
        # Process the file and upload the results

        inputfile = resource["local_paths"][0]
        file_id = resource['id']
        file_name = resource['name']
        # These process messages will appear in the Clowder UI under Extractions.
        connector.message_process(resource, "Loading contents of file...")
        generate_plots(current_filepath=inputfile, current_filename=file_name)

        print('we generated plots!!')

        # TODO upload previews
        png_filepaths = []
        current_files = os.listdir(os.getcwd())
        for f in current_files:
            if f.endswith('.png'):
                png_filepaths.append(os.path.join(os.getcwd(), f))
        for png_file in png_filepaths:
            base_name = os.path.basename(png_file)
            variable_name = base_name.replace(file_name, "")
            variable_name = variable_name.lstrip('_')
            variable_name = variable_name.rstrip('.png')
            preview_id = pyclowder.files.upload_preview(connector, host, secret_key, file_id, png_file, None, "image/" + "png",
                                           visualization_name=variable_name,
                                           visualization_description=variable_name,
                                           visualization_component_id="basic-image-component")
            try:
                os.remove(png_file)
            except Exception as e:
                logger.debug(f"Error removing {png_file}")
                logger.debug(f"{e}")
        try:
            logger.debug("Cleaning up all png files")
            os.system("rm *.png")
        except Exception as e:
            logger.debug(f"Error cleaning up files {e}")


if __name__ == "__main__":
    extractor = PDG_ASJP_NetCDF()
    extractor.start()
