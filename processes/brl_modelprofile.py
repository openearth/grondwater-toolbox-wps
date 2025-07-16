# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2025 Deltares
#       Gerrit Hendriksen
#       gerrit.hendriksen@deltares.nl
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

# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/brl_modelling/processes/brl_utils_geoserver.py $
# $Keywords: $

# system pacakages
#from builtins import anext
import os
import json
from pydoc import ispackage
from pyexpat.errors import XML_ERROR_DUPLICATE_ATTRIBUTE
from turtle import shapetransform
import geojson
from shapely.geometry import shape, Point
from shutil import copyfile
from random import choice, randint

# third party
import imod

# local scripts (abbrieviation used to be from processes.brl_utils import!)
from processes.brl_utils import read_config, loguseractivity
from processes.brl_utils_vector import transformpointcoords


def mainHandler(point_json):
    """Handles the incoming point to derive information 
    from tops and bottoms and returns a sorted dictionary

    Args:
        point_json (geosjson string): geojson string with coordinat in wgs84

    Returns:
        json: json with layer order of LHM model for the specific point
    """

    # call loguseractivity
    loguseractivity('model profile')

    # preparatory work
    cf = read_config()

    #point_gjson = geojson.loads('{"type": "FeatureCollection","name": "point","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "fid": 1, "layer": 3, "area": 5000, "abstraction" : 10000  }, "geometry": { "type": "Point", "coordinates": [ 4.731298665841507, 53.0211337776002] } }]}')
    point_gjson = geojson.loads(point_json)
    
    # bear in mind, first reproject to 28992
    point = point_gjson['features'][0]['geometry']
    
    # retrieve transformed point
    y,x = point['coordinates']
    xrd,yrd = transformpointcoords(x,y)

    # get modellayers location from cf
    basepath = cf.get('Model','modeldir')
    if os.path.isdir(basepath):
        pathtopbots = os.path.join(basepath,'lagenmodel')
    
    topbots=imod.idf.open_dataset(pathtopbots+'/**/*.IDF')
    # loop over the modellayers and extract information
    dcttops = {}
    print('values in m-NAP at xy',xrd,yrd)
    for l in topbots.keys():
        selection = imod.select.points_values(topbots[l], x=xrd, y=yrd)
        dcttops[l] = float(selection.values[0])
    # store info in json
    
    marklist = sorted(dcttops.items(), key=lambda x:x[1], reverse=True)
    sortdict = dict(marklist)
    print(sortdict)
    
    res = []
    try:
        res = sortdict        
    except Exception as e:
        msg = "Error during request of data retrieval for tops and bottoms of layers!:"
        print(msg, e)
        res=[msg]
    return json.dumps(res)
