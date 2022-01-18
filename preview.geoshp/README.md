# Clowder Geoshp Metadata Extractor

Overview
geoshp extractor takes .zip input file and communicates with GeoServer (https://geoserver.ncsa.illinois.edu/geoserver/web/) to retrieve WMS metadata.

## Build a docker image
      docker build -t clowder/extractors-geoshp-preview .

## Test the docker container image:
```
      docker run --name=geoshp-preview -d
      -e 'GEOSERVER_URL=http://localhost:8080/geoserver/' 
      -e 'GEOSERVER_PASSWORD={geoserver passwd}' 
      -e 'GEOSERVER_WORKSPACE=clowder' 
      -e 'GEOSERVER_USERNAME={geoserver username}' 
      clowder/extractors-geoshp-preview
```

## To run without docker

This extractor uses the python modules GDAL.
Installing GDAL requires gdal libraries.
On Ubunut, do "sudo apt-get install python-gdal"; on Mac OS X, do
"brew install gdal". Then install the modules in the requirements.txt file.

While following the instructions below, please note that
on Ubuntu, installing gdal in a virtualenv seems
problematic, and using the system environment could prove easier.
The other steps are the same.

To install and run the python extractor, do the following:

1. Setup a [virtualenv](https://virtualenv.pypa.io), e.g., named "geoshp":

   `virtualenv geoshp`
2. Activate the virtualenv

   `source geoshp/bin/activate`
3. Install required python packages using *pip*

   `pip install -r requirements.txt`
4. Install pyclowder if it is not installed yet.

   `pip install git+https://opensource.ncsa.illinois.edu/stash/scm/cats/pyclowder.git`

   or if you have pyclowder checked out as well (useful when developing)

   `ln -s ../../pyClowder/pyclowder pyclowder`
5. Modify config.py 
6. Start extractor

   `./ncsa.geo.shp.py`

## Known Issues
- The WMS layer might have the wrong bouding box. The layer will be shown on the openlayers previewer but the map will
  zoom to the wrong spot. We manually reproject the bounding box (see `zipshputils.findExtent()`). Some projections use 
  reversed axis. For those we use a different formula. The list of projections requiring this is at `zipshputils.findExtent():231`. 


