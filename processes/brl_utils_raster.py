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

# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/brl_modelling/processes/brl_utils_lines.py $
# $Keywords: $
import os
from pathlib import Path
import rasterio
import numpy as np

def rasterstats_qubic(lstrasters):
    """Picks up every tif with type in the name and calculates a total sum and converts this to m3 water.

    inputs:
        dir (string)  : directory with the result of the calculation
        type (string) : what kind of output is used for the calculation of the statistics
        stats (string): what type of statistics is used for the calculation (defaults to sum)
    
    Returns:
        stats (double): the result of the statistical procedure
    """
    # Initialize an empty list to store the raster data
    total_sum = 0
    # loop over all tifs with the pattern 
    for atif in lstrasters:
        # open, read and store the data in the raster_data list
        with rasterio.open(atif) as src:
            data = src.read()

            # set nodata to 0
            data[np.isnan(data)] = 0

            # Get the no-data value from the raster metadata
            # Calculate the sum of the valid (non-no-data) values
            valid_sum = np.sum(data)
            
            # Add the sum of the current raster to the total sum
            total_sum += valid_sum

    resolution = src.res
    res = total_sum/(pow(resolution[0],2))

    return res


def test():
    lstresults = ['c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l1.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l2.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l3.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l4.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l5.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l6.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l7.tif']
    if 'diffhead' in lstresults[0]:
        print(rasterstats_qubic(lstresults))