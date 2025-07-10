# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2022 Deltares
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

# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/brl_modelling/processes/brl_wps_modelprofile.py $
# $Keywords: $

"""
describe http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=brl_wps_modelprofile&version=1.0.0
execute http://localhost:5000/wps?request=Execute&service=WPS&identifier=brl_wps_modelprofile&version=1.0.0&DataInputs=geojson_point={"type": "FeatureCollection","name": "point","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "fid": 1, "layer": 3, "area": 5000, "modelprofile" : 10000 }, "geometry": { "type": "Point", "coordinates": [ 5.780, 52.145 ] } }]}
execute http://localhost:5000/wps?request=Execute&service=WPS&identifier=brl_wps_modelprofile&version=1.0.0&DataInputs=geojson_point={"type": "FeatureCollection","name": "point","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "fid": 1, "layer": 3, "area": 2500, "modelprofile" : -5000 }, "geometry": { "type": "Point", "coordinates": [ 5.73061, 52.27429 ] } }]}
execute on server https://basisrivierbodemligging.openearth.nl/wps?request=Execute&service=WPS&identifier=brl_wps_modelprofile&version=1.0.0&DataInputs=geojson_point={"type": "FeatureCollection","name": "point","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "fid": 1, "layer": 3, "area": 5000, "modelprofile" : 10000 }, "geometry": { "type": "Point", "coordinates": [ 4.731298665841507, 53.0211337776002] } }]}
"""
# PyWPS
from pywps import Process, Format, FORMATS
from pywps.inout.inputs import ComplexInput, LiteralInput
from pywps.inout.outputs import ComplexOutput
from pywps.app.Common import Metadata

# other
import json
from datetime import datetime
# very basis logging
fn=r'.\logs\user_activity.log'
with open(fn, 'a+') as f:
	f.write(','.join([datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'modelprofile tool']))
	f.write('\n')

# local
from processes.brl_utils import *
# from processes.brl_utils_vector import *
from processes.brl_modelprofile import mainHandler


class WpsBRLmodelprofile(Process):

	def __init__(self):
		# Input [in json format ]
		inputs = [ComplexInput('geojson_point', 'Area of interest', 
                         [Format('application/json')], abstract="Complex input abstract", )]

		# Output [in json format]
		outputs = [ComplexOutput('output_json',
		                         'BRL calculate effect of modelprofiles for a certain area',
		                         supported_formats=[Format('application/json')])]

		super(WpsBRLmodelprofile, self).__init__(
		    self._handler,
		    identifier='brl_wps_modelprofile',
		    version='1.0',
		    title='backend process for the BRL tool to extract data for to create a profile of the modelinput',
		    abstract='This Groundwatertoolbox tool expects point location.',
		    profile='',
		    metadata=[Metadata('WpsBRLmodelprofile'), Metadata('BRL/water')],
		    inputs=inputs,
		    outputs=outputs,
		    store_supported=False,
		    status_supported=False
		)

	## MAIN
	def _handler(self, request, response):
		try:
			# Read input
			point_jsonstr = request.inputs["geojson_point"][0].data

			# mainHandler sets up reference groundwatermodel and scenario groundwatermodel
			# effects are subtracted and loaded into geoserver       		
			res = mainHandler(point_jsonstr)
			response.outputs['output_json'].data = json.dumps(res) 
		
		except Exception as e:
			res = { 'errMsg' : 'ERROR: {}'.format(e)}
			response.outputs['output_json'].data = json.dumps(res) 

		return response
