# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2025 Deltares
#       Joan Sala
#       joan.salacalero@deltares.nl
#
#   This library is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this library.  If not, see <http://www.gnu.org/licenses/>.
#   --------------------------------------------------------------------
#
# This tool is part of <a href="http://www.OpenEarth.eu">OpenEarthTools</a>.
# OpenEarthTools is an online collaboration to share and manage data and
# programming tools in an open source, version controlled environment.
# Sign up to recieve regular updates of this function, and to contribute
# your own tools.

# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/brl_modelling/processes/brl_utils_vector.py $
# $Keywords: $

import json
import os

# conda packages
from sqlalchemy import create_engine
import geojson
from osgeo import ogr
import pandas as pd
import geopandas as gpd
import imod
import numpy as np

import logging
LOGGER= logging.getLogger("PYWPS")


def createpointer(polygon, extent, cs):
	xmin = extent[0][0]; ymin = extent[0][1]
	xmax = extent[1][0]; ymax = extent[1][1]
	gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:28992")
	like = imod.util.empty_2d(float(cs), float(xmin), float(xmax), float(cs), float(ymin), float(ymax))
	try:
		pointer = imod.prepare.rasterize(gdf, like=like)
	except Exception as e:
		print('createpointer',e)	
	return pointer

# Get roads given an area of interest
def get_waters(cf, watersId, lines=False):
	# Check if existing selection exists [caching]
	if lines:
		outfname = os.path.join(cf.get('Settings', 'tmpdir'), watersId.rstrip()+'_lines.geojson')
	else:
		outfname = os.path.join(cf.get('Settings', 'tmpdir'), watersId.rstrip() + '.geojson')

	print('Loading: {}'.format(outfname))
	# Calculate temp roads only if necessary
	if not(os.path.exists(outfname)):
		raise ValueError('The waters layer selected does not exist')

	return outfname

def geojson_to_wkt(geojson_str):
	f = geojson.loads(geojson_str)
	g = ogr.CreateGeometryFromJson(geojson.dumps(f['geometry']))
	return g.ExportToWkt()

# Get roads as GeoJSON
def get_waters_geojson(cf, geojson_str):
	# DB connections
	engine = create_engine('postgresql+psycopg2://'+cf.get('PostGIS', 'user')
	+':'+cf.get('PostGIS', 'pass')+'@'+cf.get('PostGIS', 'host')+':'+str(cf.get('PostGIS', 'port'))
	+'/'+cf.get('PostGIS', 'db'), strategy='threadlocal')
	
#	# Get WKT string [postgis handles better]
#	area = get_area_bounds(cf, geojson_str)
	wkt_str = geojson_to_wkt(geojson_str)
	
#	buffsizedeg = float(buffsize)/111139.0
	
	# PostGIS query [extract watercourses from the table and extract polygon (the actual input, converted to RD to be used as mask for further processing within brl_utils_imod)]
	sqlStr = """SELECT ST_AsGeoJSON(ST_CENTROID(ST_Transform(ST_GeomFromText('{wkt}',4326),28992))) as centroid,
              ST_AsGeoJSON(ST_Transform(ST_GeomFromText('{wkt}',4326),28992)) as polygon, 
                ST_AsGeoJSON(
        	      ST_Intersection(
    			    ST_GeomFromText('{wkt}',4326), 
    			      ST_Union(st_transform(geom,4326)))) as lines 
                FROM vaarwegvakken WHERE ST_Intersects(st_transform(geom,4326), ST_GeomFromText('{wkt}',4326))""".format(wkt=wkt_str)
    
	# Get data and close connection [one row]
	resB = engine.execute(sqlStr)
	for r in resB:
		dataCentr = r.centroid
		dataPoly = r.polygon
		dataLines = r.lines
	resB.close()

	return dataLines,dataPoly,dataCentr

# Create a GeoJSON feature from an OGR feature
def create_feature(g):
	feat = {
		'type': 'Feature',
		'properties': {},
		'geometry': json.loads(g.ExportToJson())
	}
	return feat

def roundCoords(px, py, resolution=250):
	return round(px/resolution)*resolution, round(py/resolution)*resolution

#input is bbox dictionary of coordinates
# centre point will be calculated and with the centrepoint new extent for modelling will be created
# and rounded to modelcellsize, bbox_rd is a numpy array with the bounding box
def createmodelextent(bbox_rd,extent,cellsize=250):
	"""Convert any arbitrary rectangle box to rounded coordinates
	   this is necessary for the model, should be rounded according to cellsize		

	Args:
		bbox_rd (list/tuple): list of coordinates
		extent (integer): size of the extent
		cellsize (integer): cellsize of the model used
	Returns:
		_type_: list fo coordinates
	"""    
	lstx = [bbox_rd[0]]
	lstx.append(bbox_rd[2])
	lsty = [bbox_rd[1]]
	lsty.append(bbox_rd[3])
	x0,y0 = min(lstx),min(lsty)
	x1,y1 = max(lstx),max(lsty)
	xe0,ye0 = x0-extent,y0-extent
	xe1,ye1 = x1+extent,y1+extent
	lstext = [roundCoords(xe0,ye0,cellsize),roundCoords(xe1,ye1,cellsize)]
	return lstext

#input is bbox dictionary of coordinates
# centre point will be calculated and with the centrepoint new extent for modelling will be created
# and rounded to modelcellsize, bbox_rd is a numpy array with the bounding box
def createmodelextent_multiple(bbox_rd,extent,cellsize=250):
	"""Convert any arbitrary rectangle box to rounded coordinates
	   this is necessary for the model, should be rounded according to cellsize		

	Args:
		bbox_rd (list/tuple): list of coordinates
		extent (integer): size of the extent
		cellsize (integer): cellsize of the model used
	Returns:
		_type_: list fo coordinates
	"""    
	lstx = bbox_rd[0] + bbox_rd[2] 
	lsty = bbox_rd[1] + bbox_rd[3]
	x0,y0 = min(lstx),min(lsty)
	x1,y1 = max(lstx),max(lsty)
	xe0,ye0 = x0-extent,y0-extent
	xe1,ye1 = x1+extent,y1+extent
	lstext = [roundCoords(xe0,ye0,cellsize),roundCoords(xe1,ye1,cellsize)]
	return lstext

# this function returns the total extent of all selected watercourses
# selected watercourses are represented by a list of watersIds. Using the power
# of postgis with the first request (extract the lines from the database)
# also an extent file in rd is given
def definetotalextent(cf,watersId):
	"""_summary_

	Args:
		cf (ConfigParser object): ConfigParser object
		watersId (String): String with unique number identifying the object of interest

	Returns:
		Extent (List): list of coordinates that define the boundary of the model
	"""
 
	tmpdir = cf.get('wps', 'tmp')
	gdflist = []
    
	for wid in watersId.split(','):
        #load the watersId lines geojson
		wjs = os.path.join(tmpdir,wid+'_extent_rd.geojson')
        # add to list of geojson objects
		gdflist.append(gpd.read_file(wjs))
	bbox_rd = pd.concat(gdflist).total_bounds
	return createmodelextent(bbox_rd,1000,250)

def definetotalextent_from_polylist(polyList, buf, cs):    
    npoly = len(polyList)
    bbox_rd = np.empty([npoly,4])
    i = 0
    for poly in polyList:
        bb = poly.bounds # (xmin,ymin,xmax,ymax)
        bbox_rd[i,:] = bb
        i += 1
    bb_tuple = bbox_rd.transpose().tolist()
    return createmodelextent_multiple(bb_tuple, buf, cs)

# following function converts coordinates from EPSG:4326 - to EPSG:28992
def transformpointcoords(x,y, epsgin='WGS84',epsgout='EPSG:28992'):
    """
    convert point (geojson format) from CRSin to CRSout using pyproj

    Parameters
    ----------
    xs  : list
    	DESCRIPTION.
		input point list
    epsgin  : string 
    	DESCRIPTION.
     	value representing the epsgcode (ie. epsg:4326 for WGS84)
    epsgout : string
    	DESCRIPTION.
     	value representing the epsgcode (ie. epsg:28992 for RD-New)

    Returns
    -------
    point : list
        DESCRIPTION.
        returns a list of transformed xy coordinates
    """
    from pyproj import Proj,Transformer, CRS
    
    in_proj = CRS(epsgin)
    out_proj = CRS(epsgout)
    transformer = Transformer.from_crs(in_proj,out_proj)
    tpoint = transformer.transform(x,y)
    return tpoint
    
def transformpolygon(ajson,epsgin='EPSG:4326', epsgout='EPSG:28992'):
	"""Function to transform a vector object in geojson format to any supported spatial reference id

	Args:
		geojson (_type_): geojson object representing a polygon (line or point should also work actually)
		epsgin (str, optional): EPGS SRID code to convert from. Defaults to 'EPSG:4326'
		epsgout (str, optional): EPSG SRID code to convert to. Defaults to 'EPSG:28992'.
	"""
	import pyproj
	import geojson
	from shapely.geometry.polygon import Polygon
	from shapely.ops import transform
	ssrid = pyproj.CRS(epsgin)
	tsrid = pyproj.CRS(epsgout)

	data = geojson.loads(ajson)
	#geom = Polygon(data['geometry']['coordinates'][0])
	npoly = len(data['features'])

	polyList = []
	for ipoly in range(npoly):
		geom = Polygon(data['features'][ipoly]['geometry']['coordinates'][0])
	    #g = wkb.dumps(geom, hex=True, srid=epsgout)
	    #return(g)

	    #print(type(wkbpoly))
	    #wkbpoly = g
        # create extent around this specific point
	    # apoly = wkb.loads(wkbpoly,hex=True)
		project = pyproj.Transformer.from_crs(ssrid, tsrid, always_xy=True).transform 
		tpoly = transform(project,geom)
		polyList.append(tpoly)

	return polyList



