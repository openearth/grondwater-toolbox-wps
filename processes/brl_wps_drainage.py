# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2025 Deltares
#       Gerrit Hendriksen/Jarno Verkaik
#       gerrit.hendriksen@deltares.nl/jarno.verkaik@deltares.nl
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

# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/brl_modelling/processes/brl_wps_abstraction.py $
# $Keywords: $

"""
test server https://openearth-basis-rivierbodem-ligging-test.avi.directory.intra/wps?service=wps&version=1.0.0&request=getCapabilities
execute http://localhost:5000/wps?request=Execute&service=WPS&identifier=brl_wps_drainage&version=1.0.0&DataInputs=json_inputs={"type": "FeatureCollection","name": "test_drainage","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "fid": 1, "id": 1, "layer": 1, "drn_res": 0.1, "drn_bodh": -1.0, "outres": 25, "buffer": 1000}, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.156277399770034, 52.176580968463142 ], [ 6.144994026135112, 52.172730059457152 ], [ 6.152601459519871, 52.165249248498547 ], [ 6.165923192478923, 52.169621072903709 ], [ 6.165923192478923, 52.169621072903709 ], [ 6.156277399770034, 52.176580968463142 ] ] ] } },{ "type": "Feature", "properties": { "fid": 2, "id": 2, "layer": 2, "drn_res": 0.01, "drn_bodh": -5.0, "outres": 25, "buffer": 1000}, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.163015019979431, 52.163635417180721 ], [ 6.155382824357055, 52.158334542860608 ], [ 6.159790787936715, 52.150517307127558 ], [ 6.170599714815764, 52.149613640671049 ], [ 6.17238649730023, 52.163276133533046 ], [ 6.17238649730023, 52.163276133533046 ], [ 6.163015019979431, 52.163635417180721 ] ] ] } }]}

server
https://openearth-basis-rivierbodem-ligging-test.avi.directory.intra/wps?request=Execute&service=WPS&identifier=brl_wps_drainage&version=1.0.0&DataInputs=json_inputs={"type": "FeatureCollection","name": "test_drainage","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "fid": 1, "id": 1, "layer": 1, "drn_res": 0.1, "drn_bodh": -1.0, "outres": 25, "buffer": 1000}, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.156277399770034, 52.176580968463142 ], [ 6.144994026135112, 52.172730059457152 ], [ 6.152601459519871, 52.165249248498547 ], [ 6.165923192478923, 52.169621072903709 ], [ 6.165923192478923, 52.169621072903709 ], [ 6.156277399770034, 52.176580968463142 ] ] ] } },{ "type": "Feature", "properties": { "fid": 2, "id": 2, "layer": 2, "drn_res": 0.01, "drn_bodh": -5.0, "outres": 25, "buffer": 1000}, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.163015019979431, 52.163635417180721 ], [ 6.155382824357055, 52.158334542860608 ], [ 6.159790787936715, 52.150517307127558 ], [ 6.170599714815764, 52.149613640671049 ], [ 6.17238649730023, 52.163276133533046 ], [ 6.17238649730023, 52.163276133533046 ], [ 6.163015019979431, 52.163635417180721 ] ] ] } }]}
"""

# PyWPS
from pywps import Process, Format, FORMATS
from pywps.inout.inputs import ComplexInput, LiteralInput
from pywps.inout.outputs import ComplexOutput
from pywps.app.Common import Metadata

# other
import json

# local
# from processes.brl_utils import *
# from processes.brl_utils_vector import *
from processes.brl_drainage import mainHandler

class WpsBRLDrainage(Process):
    def __init__(self):
        # Input [in json format ]
        inputs = [
            ComplexInput("json_inputs", "id, area, layer, drn_res, drn_bodh, outres",
                [Format("application/json")],
                abstract="Complex input abstract",
            )
        ]

        # Output [in json format]
        outputs = [
            ComplexOutput(
                "output_json",
                "BRL calculate effect of drainage measures in multiple areas",
                supported_formats=[Format("application/json")],
            )
        ]

        super(WpsBRLDrainage, self).__init__(
            self._handler,
            identifier="brl_wps_drainage",
            version="1.0",
            title="backend process for the Groundwatertools to calculate effect of a change in drainage parameters",
            abstract="This Groundwatertoolbox tool expects and area drawn by a user, layer (1-7), area of interest and horizontal calculation resolution.",
            profile="",
            metadata=[Metadata("WpsBRLDrainage"), Metadata("BRL/water")],
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False,
        )

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
            #json_input = request.inputs["json_inputs"][0].data
            json_input = request.inputs["json_inputs"][0].data
            # mainHandler sets up reference groundwatermodel and scenario groundwatermodel
            # effects are subtracted and loaded into geoserver
            res = mainHandler(json_input)
            response.outputs["output_json"].data = json.dumps(res)
        # response.outputs['output_json'].data = res                 #Different to other WPS 'output_json' is not defined
        except Exception as e:
            res = {"errMsg": "ERROR: {}".format(e)}
            response.outputs["output_json"].data = json.dumps(
                res
            )  # Different to other WPS 'output_json' is not defined

        return response
