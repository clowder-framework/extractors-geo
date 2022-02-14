#!/usr/bin/python
import json
import logging
import urllib

from osgeo import osr, gdal


class Utils:

    def __init__(self, geotifffile, rasterStyleTemplate):
        self.geotiff = geotifffile
        self.rasterStyleTemplate = rasterStyleTemplate
        self.epsg = 'UNKNOWN'
        self.extent = 'UNKNOWN'
        self.isGeotiff = self.checkGeotiff()
        self.logger = logging.getLogger('geotiff')
        
        if self.isGeotiff:
            tmpEpsg = self.findProjection()
            if tmpEpsg != 'None' and tmpEpsg != None:
                self.epsg = tmpEpsg
            else:
                self.epsg = 'UNKNOWN'

            if self.epsg != 'UNKNOWN':
                extent = self.findExtent()
                if extent != 'None':
                    self.extent = extent
                else:
                    self.extent = 'UNKNOWN'

    def hasError(self):
        if (not self.isGeotiff) or  self.epsg == 'UNKNOWN' or self.extent == 'UNKNOWN':
            return True
        else:
            return False

    def getEpsg(self):
        return self.epsg

    def getExtent(self):
        return self.extent


    def checkGeotiff(self):
        isGeo = True
        try:
            ds = gdal.Open(self.geotiff)
            if ds.GetProjectionRef() == '': 
                isGeo = False
        except:
            isGeo = False
        ds = None
        return isGeo
        
    def findProjection(self):
        if not self.isGeotiff:
            self.logger.debug('findProjection: it is not a geotiff')
            return 'None'
        prj_txt=''
        prj_code=''
        try:
            ds = gdal.Open(self.geotiff)
            prj_txt = ds.GetProjectionRef()
            srs = osr.SpatialReference()
            srs.ImportFromWkt(prj_txt)
            srs.AutoIdentifyEPSG()
            prj_code=srs.GetAuthorityCode(None)
        except:
            prj_code='None'

        # close geotiff file
        ds = None

        if str(prj_code).strip() != 'None':
            return prj_code

        query = urllib.parse.urlencode({'exact':True,'error':True,'mode':'wkt','terms':prj_txt})

        try:
            webres = urllib.urlopen('http://prj2epsg.org/search.json', query.encode())
            jres = json.loads(webres.read().decode())
            if len(jres['codes']) > 0:
                self.logger.debug(jres['codes'][0]['code'])
            else:
                self.logger.debug('None')
        except:
            self.logger.debug('None')
        
        return prj_code

    def findExtent(self):
        if not self.isGeotiff:
            self.logger.debug('findExtent: it is not a geotiff')
            return 'None'
        if self.epsg == 'UNKNOWN':
            self.logger.debug('findExtent: unknown projection; could not calculate extent')
            return 'None'

        GOOGLE = 3857
        ds = gdal.Open(self.geotiff)

        dsGtrn = ds.GetGeoTransform()
        # quick fix to avoid wrong bounding box calculation when the input extent is world wide
        dsGtrn = self.validateBbox(dsGtrn)
        osrs = osr.SpatialReference()
        osrs.ImportFromWkt(ds.GetProjectionRef())
        dsrs = osr.SpatialReference()
        dsrs.ImportFromEPSG(GOOGLE)
        ct = osr.CoordinateTransformation(osrs, dsrs)
        ll = ct.TransformPoint(dsGtrn[0], dsGtrn[3])
        ur = ct.TransformPoint(dsGtrn[0] + dsGtrn[1] * ds.RasterXSize + dsGtrn[2] * ds.RasterYSize,  dsGtrn[3] + dsGtrn[4] * ds.RasterXSize + dsGtrn[5] *ds.RasterYSize)
        r = [0. for x in range(4)]
        if ll[0] < ur[0]:
            r[0] = ll[0]
            r[2] = ur[0]
        else: 
            r[0] = ur[0]
            r[2] = ll[0]
        if ll[1] < ur[1]:
            r[1] = ll[1]
            r[3] = ur[1]
        else: 
            r[1] = ur[1]
            r[3] = ll[1]

        ds = None
        return ','.join(map(str, r))

    def validateBbox(self, intuple):
        lst = list(intuple)
        tuple_changed = False

        if intuple[0] <= 180 and intuple[0] > 179:
            lst[0] = 179
            tuple_changed = True
        if intuple[0] >= -180 and intuple[0] < -179:
            lst[0] = -179
            tuple_changed = True
        if intuple[3] <= 90 and intuple[3] > 89:
            lst[3] = 89
            tuple_changed = True
        if intuple[3] >= -90 and intuple[3] < -89:
            lst[3] = -89
            tuple_changed = True

        if tuple_changed:
            return tuple(lst)
        else:
            return intuple

    def createStyle(self):
        if not self.isGeotiff:
            self.logger.debug('createStyle: it is not a geotiff')
            return 'None'
        ds = gdal.Open(self.geotiff)
        band = ds.GetRasterBand(1)
        nodataValue = band.GetNoDataValue()
        stat = band.GetStatistics(True, True)
        if not stat:
            return 'None'
        minValue = stat[2] - stat[3]*2 
        maxValue = stat[2] + stat[3]*2
        self.logger.debug('nodata ' + str(nodataValue))
        self.logger.debug('min ' + str(minValue))
        self.logger.debug('max ' + str(maxValue))
        stylefile = open(self.rasterStyleTemplate, 'r')    
        style = stylefile.read()

        minline = '<ColorMapEntry color="#000000" quantity="'+str(minValue)+'" label="min" />\n'
        maxline = '<ColorMapEntry color="#FFFFFF" quantity="'+str(maxValue)+'" label="max" />\n'
        colormaplines = ''

        validNoData = True

        if not nodataValue:
            validNoData = False 
        else:
            if nodataValue > minValue and nodataValue < maxValue:
                validNoData = False
            
        if not validNoData:
            nodataLine = '<!-- nodata value or nodata value is in range of valid data range -->\n'
            colormaplines += nodataLine
            colormaplines += minline
            colormaplines += maxline
        else:
            nodataLine = '<ColorMapEntry color="#000000" quantity="'+str(nodataValue)+'" label="nodata" opacity="0.0" />\n'
            if nodataValue <= minValue:
                colormaplines += nodataLine
                colormaplines += minline
                colormaplines += maxline
            if nodataValue >= maxValue:
                colormaplines += minline
                colormaplines += maxline
                colormaplines += nodataLine
        
        style = style.replace('<<<colormap>>>', colormaplines)
        return style
            

if __name__ == "__main__":
    source = "jong.tif"
    geo = Utils(source)
    print(geo.createStyle())
