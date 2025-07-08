# -*- coding: utf-8 -*-
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
getcapbailities http://localhost:5000/wps?request=GetCapabilities&service=WPS&version=1.0.0
describe process: http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=brl_gwmodel&version=1.0.0
execute http://localhost:5000/wps?request=Execute&service=WPS&identifier=brl_gwmodel&version=1.0.0&DataInputs=configuration={"riverbedDifference":-2,"extent":5,"calculationLayer":1,"visualisationLayer":1},{"riverbedDifference":-2,"extent":5,"calculationLayer":1,"visualisationLayer":1};waters_identifier=waters_1605522428478957,waters_1605264602921628
http://localhost:5000/wps?request=Execute&service=WPS&identifier=brl_gwmodel&version=1.0.0&DataInputs=configuration={"riverbedDifference":-10,"extent":5,"calculationLayer":1,"visualisationLayer":1};waters_identifier=waters_1708330543639290
https://basisrivierbodemligging.openearth.nl/wps?request=Execute&service=WPS&identifier=brl_gwmodel&version=1.0.0&DataInputs=configuration={"riverbedDifference":-2,"extent":5,"calculationLayer":1,"visualisationLayer":1};waters_identifier=waters_1573832155882882

Based on user choices (selection of waterways) calculates the effect of measures.
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
from processes.brl_utils_imod import mainHandler

class WpsBRLGWModel(Process):

	def __init__(self):
		# Input [in json format ]
		inputs = [LiteralInput('waters_identifier', 'Identifier of the selected watercourses given by the wps_watercourses function', data_type='string'),
				  ComplexInput('configuration', 'setup for the modelling process',
		                       [Format('application/json')],
		                       abstract="Complex input abstract", ),]

		# Output [in json format]
		outputs = [ComplexOutput('output_json',
		                         'BRL global configuration and settings',
		                         supported_formats=[Format('application/json')])]

		super(WpsBRLGWModel, self).__init__(
		    self._handler,
		    identifier='brl_gwmodel',
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
			# Read configuration
			cf = read_config()

			# read the input:
			# watersId is a list                
			# model_setup is a list of jsons
			watersId = request.inputs["waters_identifier"][0].data
			print(watersId)
			model_setup = request.inputs["configuration"][0].data
			print(model_setup)   
			
			# call the procedure
			#wmslayer = 'maaiveld:maaiveld'
			# old way, changed at 07-07-2023
			#wmslayer = mainHandler(cf,model_setup,watersId)
			#response.outputs['output_json'].data = write_output(cf, wmslayer,'brl')

			# in this way it is similar to the abstraction and digit
			res = mainHandler(cf,model_setup,watersId)
			response.outputs['output_json'].data = json.dumps(res)
		except Exception as e:
			res = { 'errMsg' : 'ERROR: {}'.format(e) }
			response.outputs['output_json'].data = json.dumps(res)
		return response