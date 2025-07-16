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

# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/brl_modelling/processes/brl_wps_abstraction.py $
# $Keywords: $

"""
describe http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=brl_wps_digit&version=1.0.0
exectute http://localhost:5000/wps?request=Execute&service=WPS&identifier=brl_wps_digit&version=1.0.0&DataInputs=json_inputs={"type": "FeatureCollection","name": "test_digit","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "fid": 1, "area": 1000, "layer": 1, "depth": -10.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.162896776408417, 52.172254558612124 ], [ 6.1571531476448, 52.165871708003593 ], [ 6.16878182055842, 52.163091860336294 ], [ 6.171535672342853, 52.17126815383174 ], [ 6.171535672342853, 52.17126815383174 ], [ 6.162896776408417, 52.172254558612124 ] ] ] } }]}

production server https://basisrivierbodemligging.openearth.nl/wps?request=Execute&service=WPS&identifier=brl_wps_digit&version=1.0.0&DataInputs=json_inputs={"type": "FeatureCollection","name": "test_digit","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "fid": 1, "area": 1000, "layer": 1, "depth": -10.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.162896776408417, 52.172254558612124 ], [ 6.1571531476448, 52.165871708003593 ], [ 6.16878182055842, 52.163091860336294 ], [ 6.171535672342853, 52.17126815383174 ], [ 6.171535672342853, 52.17126815383174 ], [ 6.162896776408417, 52.172254558612124 ] ] ] } }]}
test server https://openearth-basis-rivierbodem-ligging-test.avi.directory.intra/wps?request=Execute&service=WPS&identifier=brl_wps_digit&version=1.0.0&DataInputs=json_inputs={"type": "FeatureCollection","name": "test_digit","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "fid": 1, "area": 1000, "layer": 1, "depth": -10.0 }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.162896776408417, 52.172254558612124 ], [ 6.1571531476448, 52.165871708003593 ], [ 6.16878182055842, 52.163091860336294 ], [ 6.171535672342853, 52.17126815383174 ], [ 6.171535672342853, 52.17126815383174 ], [ 6.162896776408417, 52.172254558612124 ] ] ] } }]}

{geojson_area={"id":"88c50716c0288377dcec68e5e0f010c4","type":"Feature","properties":{"layer": 3, "area": 1000, "depth" : 2},"geometry":{"coordinates":[[[6.1289, 52.2557],[6.1561, 52.2407],[6.1634, 52.2511],[6.1368, 52.2650],[6.1289, 52.2557],[6.1289, 52.2557]]],"type":"Polygon"}}
"""

# PyWPS
from pywps import Process, Format, FORMATS
from pywps.inout.inputs import ComplexInput, LiteralInput
from pywps.inout.outputs import ComplexOutput
from pywps.app.Common import Metadata

# local
import json
# from processes.brl_utils import *
# from processes.brl_utils_vector import *
from processes.brl_digit import mainHandler


class WpsBRLDigit(Process):
    def __init__(self):
        # Input [in json format ]
        inputs = [
            ComplexInput(
                "json_inputs",
                "Area of interest, area, depth, layer",
                [Format("application/json")],
                abstract="Complex input abstract",
            )
        ]

        # Output [in json format]
        outputs = [
            ComplexOutput(
                "output_json",
                "BRL calculate effect of digging in mud for a certain area",
                supported_formats=[Format("application/json")],
            )
        ]

        super(WpsBRLDigit, self).__init__(
            self._handler,
            identifier="brl_wps_digit",
            version="1.0",
            title="backend process for the BRL tool to calculate effect of excavation of certain modellayers",
            abstract="This Groundwatertoolbox tool expects, area drawn by user, layer (1-7), area of interest.",
            profile="",
            metadata=[Metadata("WpsBRLDigit"), Metadata("BRL/water")],
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False,
        )

    ## MAIN
    def _handler(self, request, response):
        try:
            # Read input
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
