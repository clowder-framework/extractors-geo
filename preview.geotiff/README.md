# Clowder GeoTiff Metadata Extractor

Overview

GeoTIFF is a public domain metadata standard which allows georeferencing information to be embedded within a TIFF file.

GeoTiff extractor communicates with GeoServer (https://geoserver.ncsa.illinois.edu/geoserver/web/) to get WMS metadata.

## Build a docker image
      docker build -t clowder/extractors-geotiff-preview .

## Test the docker container image:
```
      docker run --name=geotiff-preview -d
      -e 'GEOSERVER_URL=http://localhost:8080/geoserver/' 
      -e 'GEOSERVER_PASSWORD={geoserver passwd}' 
      -e 'GEOSERVER_WORKSPACE=clowder' 
      -e 'GEOSERVER_USERNAME={geoserver username}' 
      clowder/extractors-geotiff-preview
```

## To run without docker

This extractor uses the python modules GDAL.
Installing requires gdal libraries.
On Ubunut, do "sudo apt-get install python-gdal"; on Mac OS X, do
"brew install gdal". Then install the modules in the requirements.txt file.

While following the instructions below, please note that
on Ubuntu, installing gdal in a virtualenv seems
problematic, and using the system environment could prove easier.
The other steps are the same.

To install and run the python extractor, do the following:

1. Setup a [virtualenv](https://virtualenv.pypa.io), e.g., named "geotiff":

   `virtualenv geotiff`
2. Activate the virtualenv

   `source geotiff/bin/activate`
3. Install required python packages using *pip*

   `pip install -r requirements.txt`
4. Install pyclowder if it is not installed yet.

   `pip install git+https://opensource.ncsa.illinois.edu/stash/scm/cats/pyclowder.git`

   or if you have pyclowder checked out as well (useful when developing)

   `ln -s ../../pyClowder/pyclowder pyclowder`
5. Modify config.py
6. Start extractor

   `./ncsa.geo.tiff.py`


