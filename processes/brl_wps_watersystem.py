f# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2019 Deltares
#       Gerrit Hendriksen
#       Gerrit Hendriksen@deltares.nl
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

# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/brl_modelling/processes/brl_gwmodel.py $
# $Keywords: $

# ------------
# this is the new version, for multiple measures on the same watercourse or different watercourses.
# ------------

"""
getcapabilities: http://localhost:5000/wps?request=GetCapabilities&service=WPS&version=1.0.0
excute http://localhost:5000/wps?request=Execute&service=WPS&identifier=brl_wps_watersystem&version=1.0.0&DataInputs=configuration={"type": "FeatureCollection","name": "test_watersystem","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "id": 1, "h_stageDiff": 1.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 0.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": 0.0, "t_stageDiff": 0.0, "t_resisDiff": 0.0, "t_rbotDiff": 0.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 5.933101788423746, 52.243231454360838 ], [ 5.950456278773696, 52.257803058194938 ], [ 5.96885729529638, 52.255400227647158 ], [ 5.984024380008512, 52.230645548678289 ], [ 5.928754294798284, 52.195692953850397 ], [ 5.890679116858143, 52.23210880175305 ], [ 5.933101788423746, 52.243231454360838 ] ] ] } },{ "type": "Feature", "properties": { "id": 2, "h_stageDiff": 0.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 100.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": 0.0, "t_stageDiff": 0.0, "t_resisDiff": 0.0, "t_rbotDiff": 0.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.02567926827337, 52.245080865097059 ], [ 6.060995819984944, 52.254139325852059 ], [ 6.097013323530204, 52.227449571918761 ], [ 6.06069094357945, 52.206325056841663 ], [ 6.020149502532987, 52.209634345569768 ], [ 6.02567926827337, 52.245080865097059 ] ] ] } },{ "type": "Feature", "properties": { "id": 3, "h_stageDiff": 0.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 0.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": -1.0, "t_stageDiff": 0.0, "t_resisDiff": 0.0, "t_rbotDiff": 0.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 5.961611856593811, 52.180884298052646 ], [ 6.020867325350291, 52.171840288287221 ], [ 6.016331124771678, 52.146670971709192 ], [ 5.961891559011728, 52.13769409927508 ], [ 5.961611856593811, 52.180884298052646 ] ] ] } },{ "type": "Feature", "properties": { "id": 4, "h_stageDiff": 0.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 0.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": 0.0, "t_stageDiff": 1.0, "t_resisDiff": 0.0, "t_rbotDiff": -1.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.059826245638952, 52.176766125946415 ], [ 6.079673697569802, 52.189248108981758 ], [ 6.116306282235237, 52.17848720436956 ], [ 6.122256274407738, 52.158912233872641 ], [ 6.091295123560775, 52.157044505181126 ], [ 6.059826245638952, 52.176766125946415 ] ] ] } }]}

Based on user choices (selection of waterways) calculates the effect of measures.
http://localhost:5000/wps?request=Execute&service=WPS&identifier=brl_wps_watersystem&version=1.0.0&DataInputs=configuration={"type": "FeatureCollection","name": "test_watersystem","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "id": 1, "h_stageDiff": 1.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 0.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": 0.0, "t_stageDiff": 0.0, "t_resisDiff": 0.0, "t_rbotDiff": 0.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 5.933101788423746, 52.243231454360838 ], [ 5.950456278773696, 52.257803058194938 ], [ 5.96885729529638, 52.255400227647158 ], [ 5.984024380008512, 52.230645548678289 ], [ 5.928754294798284, 52.195692953850397 ], [ 5.890679116858143, 52.23210880175305 ], [ 5.933101788423746, 52.243231454360838 ] ] ] } },{ "type": "Feature", "properties": { "id": 2, "h_stageDiff": 0.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 100.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": 0.0, "t_stageDiff": 0.0, "t_resisDiff": 0.0, "t_rbotDiff": 0.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.02567926827337, 52.245080865097059 ], [ 6.060995819984944, 52.254139325852059 ], [ 6.097013323530204, 52.227449571918761 ], [ 6.06069094357945, 52.206325056841663 ], [ 6.020149502532987, 52.209634345569768 ], [ 6.02567926827337, 52.245080865097059 ] ] ] } },{ "type": "Feature", "properties": { "id": 3, "h_stageDiff": 0.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 0.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": -1.0, "t_stageDiff": 0.0, "t_resisDiff": 0.0, "t_rbotDiff": 0.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 5.961611856593811, 52.180884298052646 ], [ 6.020867325350291, 52.171840288287221 ], [ 6.016331124771678, 52.146670971709192 ], [ 5.961891559011728, 52.13769409927508 ], [ 5.961611856593811, 52.180884298052646 ] ] ] } },{ "type": "Feature", "properties": { "id": 4, "h_stageDiff": 0.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 0.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": 0.0, "t_stageDiff": 1.0, "t_resisDiff": 0.0, "t_rbotDiff": -1.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.059826245638952, 52.176766125946415 ], [ 6.079673697569802, 52.189248108981758 ], [ 6.116306282235237, 52.17848720436956 ], [ 6.122256274407738, 52.158912233872641 ], [ 6.091295123560775, 52.157044505181126 ], [ 6.059826245638952, 52.176766125946415 ] ] ] } }]}
https://openearth-basis-rivierbodem-ligging-test.avi.directory.intra/wps?request=Execute&service=WPS&identifier=brl_wps_watersystem&version=1.0.0&DataInputs=configuration={"type": "FeatureCollection","name": "test_watersystem","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "id": 1, "h_stageDiff": 1.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 0.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": 0.0, "t_stageDiff": 0.0, "t_resisDiff": 0.0, "t_rbotDiff": 0.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 5.933101788423746, 52.243231454360838 ], [ 5.950456278773696, 52.257803058194938 ], [ 5.96885729529638, 52.255400227647158 ], [ 5.984024380008512, 52.230645548678289 ], [ 5.928754294798284, 52.195692953850397 ], [ 5.890679116858143, 52.23210880175305 ], [ 5.933101788423746, 52.243231454360838 ] ] ] } },{ "type": "Feature", "properties": { "id": 2, "h_stageDiff": 0.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 100.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": 0.0, "t_stageDiff": 0.0, "t_resisDiff": 0.0, "t_rbotDiff": 0.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.02567926827337, 52.245080865097059 ], [ 6.060995819984944, 52.254139325852059 ], [ 6.097013323530204, 52.227449571918761 ], [ 6.06069094357945, 52.206325056841663 ], [ 6.020149502532987, 52.209634345569768 ], [ 6.02567926827337, 52.245080865097059 ] ] ] } },{ "type": "Feature", "properties": { "id": 3, "h_stageDiff": 0.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 0.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": -1.0, "t_stageDiff": 0.0, "t_resisDiff": 0.0, "t_rbotDiff": 0.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 5.961611856593811, 52.180884298052646 ], [ 6.020867325350291, 52.171840288287221 ], [ 6.016331124771678, 52.146670971709192 ], [ 5.961891559011728, 52.13769409927508 ], [ 5.961611856593811, 52.180884298052646 ] ] ] } },{ "type": "Feature", "properties": { "id": 4, "h_stageDiff": 0.0, "h_resisDiff": 0.0, "h_rbotDiff": 0.0, "p_stageDiff": 0.0, "p_resisDiff": 0.0, "p_rbotDiff": 0.0, "s_stageDiff": 0.0, "s_resisDiff": 0.0, "s_rbotDiff": 0.0, "t_stageDiff": 1.0, "t_resisDiff": 0.0, "t_rbotDiff": -1.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.059826245638952, 52.176766125946415 ], [ 6.079673697569802, 52.189248108981758 ], [ 6.116306282235237, 52.17848720436956 ], [ 6.122256274407738, 52.158912233872641 ], [ 6.091295123560775, 52.157044505181126 ], [ 6.059826245638952, 52.176766125946415 ] ] ] } }]}
"""
# PyWPS
from pywps import Process, Format, FORMATS
from pywps.inout.inputs import ComplexInput, LiteralInput
from pywps.inout.outputs import ComplexOutput
from pywps.app.Common import Metadata

# other
import os
import json

# local
from processes.brl_utils import read_config, read_input, write_output
from processes.brl_watersystem import mainHandler

class WpsBRLWatersystem(Process):

	def __init__(self):
		# Input [in json format ]
		inputs = [ComplexInput('configuration', 'setup for the modelling process',
		                       [Format('application/json')],
		                       abstract="Complex input abstract", ),]

		# Output [in json format]
		outputs = [ComplexOutput('output_json',
		                         'BRL global configuration and settings',
		                         supported_formats=[Format('application/json')])]

		super(WpsBRLWatersystem, self).__init__(
		    self._handler,
		    identifier='brl_wps_watersystem',
		    version='1.0',
		    title='Starts modelling with given inputs',
		    abstract='Main configuration process for the BaseRiverBed project. The process starts an iMODFLOW Model with given inputs and replies with a WMS Layer with the output. Since 2020 BRL2 it accepts multiple input parameters and difwaters.',
		    profile='',
		    metadata=[Metadata('WpsBRLGWModelM'), Metadata('BRL/gw_model')],
		    inputs=inputs,
		    outputs=outputs,
		    store_supported=False,
		    status_supported=False
		)


	def _handler(self, request, response):

		try:
			# read the input:
			# model_setup is a list of jsons
			model_setup = request.inputs["configuration"][0].data

			# in this way it is similar to the abstraction and digit
			res = mainHandler(model_setup)
			response.outputs['output_json'].data = json.dumps(res)
		except Exception as e:
			res = { 'errMsg' : 'ERROR: {}'.format(e) }
			response.outputs['output_json'].data = json.dumps(res)
		return response