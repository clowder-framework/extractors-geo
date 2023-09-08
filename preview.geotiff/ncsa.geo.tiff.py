#!/usr/bin/env python

import logging
import os
import json
import subprocess
import tempfile
from urllib.parse import urlparse, urljoin

from pyclowder.extractors import Extractor
from pyclowder.utils import StatusMessage
from pyclowder.utils import CheckMessage
import pyclowder.files
from osgeo import gdal

import geotiffutils as gu
import gsclient as gs

from geoserver.catalog import Catalog


class ExtractorsGeotiffPreview(Extractor):
    def __init__(self):
        Extractor.__init__(self)

        # parse command line and load default logging configuration
        self.setup()

        self.extractorName = os.getenv('RABBITMQ_QUEUE', "ncsa.geotiff.preview")
        self.messageType = ["*.file.image.tiff", "*.file.image.tif"]
        self.geoServer = os.getenv('GEOSERVER_URL', 'http://localhost:8080/geoserver/')
        self.gs_username = os.getenv('GEOSERVER_USERNAME', 'admin')
        self.gs_password = os.getenv('GEOSERVER_PASSWORD', 'geoserver')
        self.proxy_url = os.getenv('PROXY_URL', 'http://localhost:9000/api/proxy/')
        self.proxy_on = os.getenv('PROXY_ON', 'false')
        self.raster_style = "rasterTemplate.xml"

        # setup logging for the exctractor
        logging.getLogger('pyclowder').setLevel(logging.DEBUG)
        logging.getLogger('__main__').setLevel(logging.DEBUG)

    def check_message(self, connector, host, secret_key, resource, parameters):
        logger = logging.getLogger('check_message')
        logger.setLevel(logging.DEBUG)
        if 'activity' in parameters:
            fileid = parameters.get('id')
            action = parameters.get('activity')
            logger.debug("activity %s for fileid %s " % (action, str(fileid)))
            if 'removed' == action:
                fileid = parameters['id']
                if 'source' in parameters:
                    mimetype = parameters.get('source').get('mimeType')
                    logger.debug("mimetype: %s for fileid %s " % (mimetype, str(fileid)))
                filename = parameters.get('source').get('extra').get('filename')
                if filename is None:
                    logger.warn('can not get filename for fileid %s' % str(fileid))

                storename = filename + '_' + str(fileid)
                layername = self.gs_workspace + ':' + storename

                logger.debug('remove layername %s' % layername)
                logger.debug("CheckMessage.ignore: activity %s for fileid %s " % (action, str(fileid)))
                self.remove_geoserver_layer(storename, layername)

                logger.debug("activity %s for fileid %s is done" % (action, str(fileid)))
                return CheckMessage.ignore
        return CheckMessage.download

    # ----------------------------------------------------------------------
    # Process the file and upload the results
    # Process the geotiff and create geoserver layer
    def process_message(self, connector, host, secret_key, resource, parameters):
        self.logger = logging.getLogger(__name__)
        isTiffType = False
        if parameters.get('source'):
            mimetype = parameters.get('source').get('mimeType')
            if mimetype == 'image/tiff' or mimetype == 'image/tif':
                isTiffType = True
        filename = resource['name']
        # add .tif to filename if filename doesnot have it.
        if isTiffType:
            extension = os.path.splitext(filename)[1].lower()
            if extension != '.tif' and extension != '.tiff':
                filename = filename + '.tif'

        inputfile = resource["local_paths"][0]
        fileid = resource['id']

        # get variable for geoserver workspace. This is a dataset's parent id
        try:
            parentid = resource['parent']['id']
        except:
            parentid = "no_datasets"
        self.gs_workspace = parentid

        tmpfile = None

        try:
            # call actual program
            result = self.extractGeotiff(inputfile, fileid, filename, secret_key)

            if not result['WMS Layer URL'] or not result['WMS Service URL'] or not result['WMS Layer URL']:
                self.logger.info('[%s], inputfile: %s has empty result', fileid, inputfile)

            # store results as metadata
            if not result['isGeotiff'] or len(result['errorMsg']) > 0:
                # channel = parameters['channel']
                # header = parameters['header']
                for i in range(len(result['errorMsg'])):
                    connector.status_update(StatusMessage.error, {"type": "file", "id": fileid},
                                            result['errorMsg'][i])
                    self.logger.info('[%s] : %s', fileid, result['errorMsg'][i], extra={'fileid': fileid})
            else:
                # While running in docker, might need some magic to fix docker URL vs. external URL in metadata entries
                metadata_geo_host = os.getenv("EXTERNAL_GEOSERVER_URL", "")
                if len(metadata_geo_host) > 0:
                    internal_geo_host = os.getenv("GEOSERVER_URL", "")
                    result = {
                        'WMS Layer Name': result['WMS Layer Name'],
                        'WMS Service URL': result['WMS Service URL'].replace(internal_geo_host, metadata_geo_host),
                        'WMS Layer URL': result['WMS Layer URL'].replace(internal_geo_host, metadata_geo_host)
                    }
                else:
                    result = {
                        'WMS Layer Name': result['WMS Layer Name'],
                        'WMS Service URL': result['WMS Service URL'],
                        'WMS Layer URL': result['WMS Layer URL']
                    }
                metadata = self.get_metadata(result, 'file', fileid, host)

                # register geotiff WMS layers with Clowder
                CLOWDER_VERSION = os.getenv("CLOWDER_VERSION", 1)
                if int(CLOWDER_VERSION) == 2:
                    # upload visualization URL
                    payload = json.dumps({
                        "resource": {
                            "collection": "files",
                            "resource_id": fileid
                        },
                        "client": host,
                        "parameters": result,
                        "visualization_mimetype": "image/tiff",
                        "visualization_component_id": "geoserver-viewer-component"
                    })
                    headers = {
                        "X-API-KEY": secret_key,
                        "Content-Type": "application/json"
                    }
                    host = os.getenv("CLOWDER_URL", host)
                    connector.post('%sapi/v2/visualizations/config' % host, headers=headers, data=payload,
                                   verify=connector.ssl_verify if connector else True)
                else:
                    (_, ext) = os.path.splitext(inputfile)
                    (_, tmpfile) = tempfile.mkstemp(suffix=ext)
                    host = os.getenv("CLOWDER_URL", host)
                    pyclowder.files.upload_metadata(connector, host, secret_key, fileid, metadata)
                    self.logger.debug("upload file metadata")

        except:
            self.logger.exception("Error uploading metadata")
        finally:
            try:
                os.remove(tmpfile)
                self.logger.debug("delete tmpfile: " + tmpfile)
            except:
                pass

    def remove_geoserver_layer(self, storename, layername):
        last_charactor = self.geoServer[-1]
        if last_charactor == '/':
            geoserver_rest = self.geoServer + 'rest'
        else:
            geoserver_rest = self.geoServer + '/rest'
        cat = Catalog(geoserver_rest, username=self.gs_username, password=self.gs_password)
        # worksp = cat.get_workspace(gs_workspace)
        store = cat.get_store(storename)
        layer = cat.get_layer(layername)
        try:
            cat.delete(layer)
            cat.reload()
            cat.delete(store)
            cat.reload()
        except:
            self.logger.error("Failed to remove from geoserver")

    def extractGeotiff(self, inputfile, fileid, filename, secret_key):
        storeName = fileid
        msg = {}
        msg['errorMsg'] = []
        msg['WMS Layer Name'] = ''
        msg['WMS Service URL'] = ''
        msg['WMS Layer URL'] = ''
        msg['isGeotiff'] = False

        uploadfile = inputfile

        geotiffUtil = gu.Utils(uploadfile, self.raster_style)

        if not geotiffUtil.hasError():
            subprocess.check_call(['/usr/bin/gdaladdo'] +
                                  os.getenv("GDALADDO_ARGS", "").split() +
                                  [inputfile] +
                                  os.getenv("GDALADDO_LEVELS", "2").split())

            msg['isGeotiff'] = True
            # TODO if the proxy is working, gsclient host should be changed to proxy server
            gsclient = gs.Client(self.geoServer, self.gs_username, self.gs_password)

            if self.proxy_on.lower() == 'true':
                parsed_uri = urlparse(self.geoServer)
                gs_domain = u'{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
                geoserver_rest = self.geoServer.replace(gs_domain, self.proxy_url)
            else:
                geoserver_rest = self.geoServer

            if not geoserver_rest.endswith("rest"):
                if geoserver_rest.endswith("/"):
                    geoserver_rest += "rest"
                else:
                    geoserver_rest += "/rest"

            epsg = "EPSG:" + str(geotiffUtil.getEpsg())
            style = None

            # check if the input geotiff has a style,
            # you can do this by checking if there is any color table
            uploadfile_dataset = gdal.Open(uploadfile)
            uploadfile_band = uploadfile_dataset.GetRasterBand(1)
            color_table = uploadfile_band.GetColorTable()
            if color_table is not None:
                self.logger.debug("Geotiff has the style already")
            else:
                style = geotiffUtil.createStyle()
                self.logger.debug("style created")

            # merge file name and id and make a new store name
            combined_name = filename + "_" + storeName

            success = gsclient.uploadGeotiff(geoserver_rest, self.gs_workspace, combined_name, uploadfile, filename, style, epsg, secret_key, self.proxy_on)

            if success:
                self.logger.debug("upload geotiff successfully")
                metadata = gsclient.mintMetadataWithoutGeoserver(self.gs_workspace, combined_name, geotiffUtil.getExtent())
                # metadata = gsclient.mintMetadata(self.gs_workspace, combined_name, geotiffUtil.getExtent())
                self.logger.debug("mintMetadata obtained")
                if len(metadata) == 0:
                    msg['errorMsg'].append("Coulnd't generate metadata")
                else:
                    msg['WMS Layer Name'] = metadata['WMS Layer Name']
                    if self.proxy_on.lower() == 'true':
                        msg['WMS Service URL'] = urljoin(self.proxy_url, 'geoserver/wms')
                        # create layer url by switching geoserver url to geoserver proxy url
                        wms_layer_url = metadata['WMS Layer URL']
                        parsed_uri = urlparse(wms_layer_url)
                        gs_domain = u'{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
                        wms_layer_url = wms_layer_url.replace(gs_domain, self.proxy_url)
                        msg['WMS Layer URL'] = wms_layer_url
                    else:
                        msg['WMS Service URL'] = metadata['WMS Service URL']
                        msg['WMS Layer URL'] = metadata['WMS Layer URL']
            else:
                msg['errorMsg'].append("Fail to upload the file to geoserver")
        else:
            if not geotiffUtil.isGeotiff:
                msg['isGeotiff'] = False
                msg['errorMsg'].append("Normal TIFF file")
                return msg

            if geotiffUtil.getEpsg() == 'UNKNOWN':
                msg['errorMsg'].append("The projection could not be recognized")

            if geotiffUtil.getExtent() == 'UNKNOWN':
                msg['errorMsg'].append("The extent could not be calculated")

        return msg


if __name__ == "__main__":
    extractor = ExtractorsGeotiffPreview()
    extractor.start()
