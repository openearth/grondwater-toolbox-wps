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
import xml.etree.ElementTree as ET


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

def raster_bounds_sld(lstrasters):
    """_summary_

    Args:
        lstrasters (list): List with full file paths to rasterfiles

    Returns:
        min_val (double): double precision number for minimum value of all rasters in the list
        max_val (double): double precision number for maximum value of all rasters in the list
    """
    # Load GeoTIFFs and compute min and max
    for frst in lstrasters:
        with rasterio.open(frst) as src:
            data = src.read()  # Read the first band
            # set nodata to 0
            data[np.isnan(data)] = 0

            # derive min and max values for each raster
            min_val = np.min(data)
            max_val = np.max(data)
            return min_val, max_val


def set_dynamic_sld(sld, scnpath, min_val, max_val):
    # ***** THIS IS A NOT WORKING PART! ***** 
    # Define stepsize
    step = ((max_val-min_val)/13)

    # Generate the quantities and labels
    quantities = np.arange(min_val, max_val + step, step)
    
    # Parse the XML
    with open(sld, 'r') as file:
        data = file.read()

    # Replace the quantities and labels
    for i in range(0,14):
        data = data.format('q'+str(i) == quantities[i])
    
    # Write the modified XML to a new file
    tmp_sld = os.path.join(scnpath,os.path.basename(sld).replace('rel',scnpath.split('\\')[-1]))
    #tree.write(tmp_sld)
    return tmp_sld


def test_rstbounds():
    lstrasters = [r"C:\temp\brl\znkuoqsmwrqg\ref_head_1756997716080674_l1.tif", r"C:\temp\brl\znkuoqsmwrqg\ref_head_1756997716080674_l2.tif", r"C:\temp\brl\znkuoqsmwrqg\ref_head_1756997716080674_l3.tif", r"C:\temp\brl\znkuoqsmwrqg\ref_head_1756997716080674_l4.tif", r"C:\temp\brl\znkuoqsmwrqg\ref_head_1756997716080674_l5.tif", r"C:\temp\brl\znkuoqsmwrqg\ref_head_1756997716080674_l6.tif", r"C:\temp\brl\znkuoqsmwrqg\ref_head_1756997716080674_l7.tif", r"C:\temp\brl\hmsnlsrmc\scen_head_1756997716080674_l1.tif", r"C:\temp\brl\hmsnlsrmc\scen_head_1756997716080674_l2.tif", r"C:\temp\brl\hmsnlsrmc\scen_head_1756997716080674_l3.tif", r"C:\temp\brl\hmsnlsrmc\scen_head_1756997716080674_l4.tif", r"C:\temp\brl\hmsnlsrmc\scen_head_1756997716080674_l5.tif", r"C:\temp\brl\hmsnlsrmc\scen_head_1756997716080674_l6.tif", r"C:\temp\brl\hmsnlsrmc\scen_head_1756997716080674_l7.tif"]
    min_val, max_val = raster_bounds_sld(lstrasters)
    print(min_val, max_val)
    scnpath = r'C:\temp\brl\hmsnlsrmc'
    sld = r'C:\develop\grondwater-toolbox-wps\data\maaiveld_tov_nap_rel.sld'
    tmpsld = set_dynamic_sld(sld, scnpath, min_val, max_val)

def test():
    lstresults = ['c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l1.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l2.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l3.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l4.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l5.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l6.tif', 'c:\\temp\\brl\\xqwnggbnrr\\dif_head_1753104673110787_l7.tif']
    if 'diffhead' in lstresults[0]:
        print(rasterstats_qubic(lstresults))
