#!/usr/bin/python
import sys
import json
import urllib
from osgeo import osr
from osgeo import ogr
import tempfile
import subprocess
import shutil
import errno
import os
import os.path

class Utils:
	zipUtil = "/usr/bin/7z"

	def __init__(self, shpzipfile, zipUtil="/usr/bin/7z"):
		self.zipUtil = zipUtil
		self.shpzipfile = shpzipfile

		self.zipShpProp = {}
		self.zipShpProp['hasError'] = False
		self.zipShpProp['hasDir'] = False
		self.zipShpProp['shpFile'] = None
		self.zipShpProp['shxFile'] = None
		self.zipShpProp['dbfFile'] = None
		self.zipShpProp['prjFile'] = None
		self.zipShpProp['shpName'] = None
		self.zipShpProp['hasSameName'] = True
		self.zipShpProp['numShp'] = 0
		self.zipShpProp['targetZip'] = None
		self.zipShpProp['epsg'] = 'UNKNOWN'
		self.zipShpProp['extent'] = 'UNKNOWN'


		# create temp directory
		print "Creating temp dir ...",
		self.tempDir = tempfile.mkdtemp()
		print self.tempDir, "[DONE]"

		# unzip compressed file
		print "Uncompress the file ...", 
		subprocess.check_call([zipUtil,'x','-o%s' % self.tempDir, shpzipfile], shell=False)
		print shpzipfile, "[DONE]"

		# check the self.zipShpProp
		self.files = [os.path.join(self.tempDir,f) for f in os.listdir(self.tempDir) ]	
		
		if not self.checkZipShp():
			# find projection
			epsg_code = self.findProjection()
			if epsg_code != 'None':
				self.zipShpProp['epsg'] = epsg_code
			else:
				self.zipShpProp['epsg'] = 'UNKNOWN'

			# find extent
			if self.zipShpProp['epsg'] != 'UNKNOWN':
				extent = self.findExtent()
				if extent != 'None':
					self.zipShpProp['extent'] = extent
				else:
					self.zipShpProp['extent'] = 'UNKNOWN'
			if self.zipShpProp['epsg'] == 'UNKNOWN' or self.zipShpProp['extent'] == 'UNKNOWN':
				self.zipShpProp['hasError'] = True

	def __del__(self):
		# delete the temp dir
		if self.tempDir != None:
			try:
				import shutil
				print "Deleting temp dir ", self.tempDir
				shutil.rmtree(self.tempDir)
			except OSError as exc:
				if exc.errno != errno.ENOENT:
					raise			

	def hasError(self):
		return self.zipShpProp['hasError']

	def getEpsg(self):
		return self.zipShpProp['epsg']

	def getExtent(self):
		return self.zipShpProp['extent']

	def checkZipShp(self):
		for f in self.files:
			name, ext = os.path.splitext(os.path.basename(f))
			if (os.path.isdir(f)): 
				self.zipShpProp['hasDir'] = True
				self.zipShpProp['hasError'] = True
				continue

			if(ext.lower() == '.shp'): 
				self.zipShpProp['numShp'] = self.zipShpProp['numShp'] + 1 
				self.zipShpProp['shpFile'] = f
				if self.zipShpProp['shpName'] == None:
					self.zipShpProp['shpName'] = name
				else:
					if(self.zipShpProp['shpName'] != name): 
						self.zipShpProp['hasSameName'] = False
						self.zipShpProp['hasError'] = True
						self.zipShpProp['shpName'] = name
						
			if(ext.lower() == '.shx'): 
				self.zipShpProp['shxFile'] = f
				if self.zipShpProp['shpName'] == None:
					self.zipShpProp['shpName'] = name
				else:
					if(self.zipShpProp['shpName'] != name): 
						self.zipShpProp['hasSameName'] = False
						self.zipShpProp['hasError'] = True

			if(ext.lower() == '.dbf'):
				self.zipShpProp['dbfFile'] = f
				if self.zipShpProp['shpName'] == None:
					self.zipShpProp['shpName'] = name
				else:
					if(self.zipShpProp['shpName'] != name): 
						self.zipShpProp['hasSameName'] = False
						self.zipShpProp['hasError'] = True

			if(ext.lower() == '.prj'): 
				self.zipShpProp['prjFile'] = f
				if self.zipShpProp['shpName'] == None:
					self.zipShpProp['shpName'] = name
				else:
					if(self.zipShpProp['shpName'] != name): 
						self.zipShpProp['hasSameName'] = False
						self.zipShpProp['hasError'] = True
			
		if self.zipShpProp['shpFile'] == None or self.zipShpProp['shxFile'] == None or self.zipShpProp['dbfFile'] == None or self.zipShpProp['prjFile'] == None:
			self.zipShpProp['hasError'] = True

		if self.zipShpProp['numShp'] > 1:
			self.zipShpProp['hasError'] = True

		return self.zipShpProp['hasError']

	def findProjection(self):
		if self.zipShpProp['hasError']:
			print 'findProjection: Zipped Shapefile has error'
			return None

		prj_file = open(self.zipShpProp['prjFile'], 'r')
		prj_txt = prj_file.read()
		prj_file.close()
		prj_code = 'None'

		try:
			srs = osr.SpatialReference()
			srs.ImportFromESRI([prj_txt])
			srs.AutoIdentifyEPSG()
			prj_code=srs.GetAuthorityCode(None)
		except:
			prj_code = 'None'
	
		if str(prj_code).strip() != 'None':
			return prj_code

		query = urllib.urlencode({'exact':True,'error':True,'mode':'wkt','terms':prj_txt})

		try:
			webres = urllib.urlopen('http://prj2epsg.org/search.json', query.encode())
			jres = json.loads(webres.read().decode())
			if len(jres['codes']) > 0: 
				prj_code = jres['codes'][0]['code']
			else: 
				prj_code = 'None'
		except:
			prj_code = 'None'
		
		return prj_code
	
	def findExtent(self):
		if self.zipShpProp['hasError']:
			print 'findExtent: Zipped Shapefile has error'
			return 'None'
		if self.zipShpProp['epsg'] == 'UNKNOWN':
			print 'findExtent: Unknown projection; could not calculate extent'
			return 'None'

		shpfile = ogr.Open(self.zipShpProp['shpFile'])
		osrs = osr.SpatialReference()
		osrs.ImportFromEPSG(int(self.zipShpProp['epsg']))
		dsrs = osr.SpatialReference()
		dsrs.ImportFromEPSG(3857) # google projeciton in epsg code
		ct = osr.CoordinateTransformation(osrs, dsrs)
		layer = shpfile.GetLayer(0)
		a = layer.GetExtent()
		ab = ct.TransformPoint(a[0],a[2],0)
		cd = ct.TransformPoint(a[1],a[3],0)
		r= [ab[0], ab[1], cd[0], cd[1]]

		return ','.join(map(str,r))

	def createZip(self, destinationDir):
		if self.zipShpProp['hasError']:
			print 'createZip: Zipped Shapefile has error'
			return None
		# rezip the files in zip format if it is not a zip file
		self.zipShpProp['targetZip'] = os.path.join(destinationDir, self.zipShpProp['shpName']+'.zip')
		subprocess.check_call([self.zipUtil,'a','-tzip', self.zipShpProp['targetZip'], self.tempDir+'/*'], shell=False)
		return self.zipShpProp['targetZip']


if __name__ == "__main__":
	source  = "gltg.7z"
	zipshp = Utils(source)
	zipshp2 = Utils("gltg-folder.7z")

	if not zipshp.hasError():
		print zipshp.zipShpProp
		zipshp.createZip('.')
	print zipshp2.hasError()
	print zipshp2.zipShpProp
