 # -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2025 Deltares
#       Tess op den Kelder
#       Gerrit Hendriksen
#       tess.op.den.kelder@deltares.nl
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

"""
In this script, the idfs are changed based on the user input.
A pointer is made to select the river cells that should be changed.
"""
import os
import numpy as np
import geopandas as gpd
import xarray as xr
import imod

import logging
LOGGER= logging.getLogger("PYWPS")


def createpointer(modeltmpdir, waters_id, rivers, tmpdir): # input_config: een lijst met per watersid een lijst met laag, parameter, waarde
    # For every waters_id, a pointer is created based on the waters_id_extent.
    # This pointer is saved as waters_id_pointer
    # Set the crs, this doesn't change
    print("createpointer",waters_id)
    acrs = '28992'

    drawn_extent = os.path.join(tmpdir,f'{waters_id}_extent_rd.geojson')
    data = gpd.read_file(drawn_extent)
    data_proj = data.copy()
    #data_proj['geometry'] = data_proj['geometry'].to_crs(epsg=crs)

    # add value for rasterisation
    data_proj['value'] = 1
    # save the file
    ashp = drawn_extent.replace('.geojson','.shp')
    data_proj.to_file(ashp,crs='EPSG:{c}'.format(c=acrs),engine='fiona')

    # get extent of the source idf
    try:
        idf0 = imod.idf.open(rivers).squeeze("layer", drop=True)
    except:
        idf0 = imod.idf.open(rivers)
    extent = imod.util.spatial_reference(idf0)

    sr = dict()
    sr['bounds'] = (extent[1],
                    extent[2],
                    extent[4],
                    extent[5])
    sr['cellsizes'] = (extent[0],extent[3])

    # create raster of extent of selection
    extent_raster = imod.prepare.gdal_rasterize(ashp, column='value',dtype=np.dtype(np.float64), spatial_reference=sr)

    # select cells within the raster that have a river.
    pointer = xr.where((extent_raster.notnull()) & (idf0.notnull()) , 1, np.nan)

    try:
        assert pointer.sum().compute().item() != 0.
    except:
        print('Error: The pointer is empty')

    #clean up intermediate files
    to_cleanup = [".shp",".cpg", ".prj", ".dbf", ".shx"]
    for i in to_cleanup:
        ashp = drawn_extent.replace('.geojson',i)
        os.unlink(ashp)
    return pointer


def adjustrivpackage(modeltmpdir, lstjsonmeasures, modeldir, tmpdir):
    # Possible adjusted parameters: stage, riverbed, conductance
    # Make a copy of the original files of these parameters
    stage_baseidf = os.path.join(modeldir,'riv/hoofdwater/PEILH_1998_2006_mean.IDF')
    riverbed_lay1_baseidf = os.path.join(modeldir,'riv/hoofdwater/both_w_l1.idf')
    riverbed_lay2_baseidf = os.path.join(modeldir,'riv/hoofdwater/both_w_l2.idf')
    cond_lay1_baseidf = os.path.join(modeldir,'riv/hoofdwater/COND_HL1_250.IDF')
    cond_lay2_baseidf = os.path.join(modeldir,'riv/hoofdwater/COND_HL2_250.IDF')

    stage = imod.idf.open(stage_baseidf)
    riverbed_lay1 = imod.idf.open(riverbed_lay1_baseidf).squeeze("layer", drop=True)
    riverbed_lay2 = imod.idf.open(riverbed_lay2_baseidf).squeeze("layer", drop=True)
    cond_lay1 = imod.idf.open(cond_lay1_baseidf)
    cond_lay2 = imod.idf.open(cond_lay2_baseidf)

    # Loop over the waters_ids, and change the parameter idfs at the location of the pointers
    # Keep on changing the same array, until all pointers have been applied
    # lstjsonmeasures =
    #       list with string of possible watersids
    #       list of json

    print('brl_utils_prepareinput - lm',lstjsonmeasures)
    lstwaterids = lstjsonmeasures[0].split(',')
    for ids in range(len(lstwaterids)):
        waters_id = lstwaterids[ids]
        lm = lstjsonmeasures[1][ids]
        print(lstjsonmeasures)
    #for waters_id in lstwaterids:
        print('before createpointer',modeltmpdir, waters_id, modeldir, tmpdir)
        pointer = createpointer(modeltmpdir, waters_id, modeldir, tmpdir)

        rivbeddif_l1 = 0.
        rivbeddif_l2 = 0.
        if 'riverbedDifference' in lm.keys(): # TODO check exacte naam in input_config
            if lm['calculationLayer'] == 1:
                rivbeddif_l1 = float(lm['riverbedDifference'])
            if lm['calculationLayer'] == 2:
                rivbeddif_l2 = float(lm['riverbedDifference'])
        print('rivbeddif_l1',rivbeddif_l1)

        riverbed_lay1 = xr.where(pointer.notnull(), riverbed_lay1 + rivbeddif_l1, riverbed_lay1)
        riverbed_lay2 = xr.where(pointer.notnull(), riverbed_lay2 + rivbeddif_l2, riverbed_lay2)

        print('bij conductance')
        condbeddif_l1 = 0.
        condbeddif_l2 = 0.
        if 'conductance' in lm.keys(): # TODO check exacte naam in input_config
            if lm['calculationLayer'] == 1:
                condbeddif_l1 = float(lm['conductance'])
            if lm['calculationLayer'] == 2:
                condbeddif_l2 = float(lm['conductance'])
        print('condbeddif_l1',condbeddif_l1)
        cond_lay1 = xr.where(pointer.notnull(), cond_lay1 + condbeddif_l1, cond_lay1)
        cond_lay2 = xr.where(pointer.notnull(), cond_lay2 + condbeddif_l2, cond_lay2)

        if 'stageDifference' in lm.keys():
            stageDifference = float(lm['stageDifference' ])
        else:
            stageDifference = 0.
        print('stageDifference',stageDifference)

        # change the correct parameters:
        stage = xr.where(pointer.notnull(), stage + stageDifference, stage)

        # cond_lay1 = xr.where(pointer.notnull(), cond_lay1 + conductanceDifference, cond_lay1)
        # cond_lay2 = xr.where(pointer.notnull(), cond_lay2 + conductanceDifference, cond_lay2)

        # riverbed_lay1 = xr.where(pointer.notnull(), riverbed_lay1 + riverbedDifference, riverbed_lay1)
        # riverbed_lay2 = xr.where(pointer.notnull(), riverbed_lay2 + riverbedDifference, riverbed_lay2)


    # write the changes to target idf
    riverbed_lay1_targetidf = os.path.join(modeltmpdir, 'both_w_l1.idf')
    riverbed_lay2_targetidf = os.path.join(modeltmpdir, 'both_w_l2.idf')
    cond_lay1_targetidf = os.path.join(modeltmpdir, 'COND_HL1_250.IDF')
    cond_lay2_targetidf = os.path.join(modeltmpdir, 'COND_HL2_250.IDF')
    stage_targetidf = os.path.join(modeltmpdir, 'PEILH_1998_2006_mean.IDF')
    print('Peilenkaart', stage_targetidf)

    # save the idf's with changes to model directory
    imod.idf.write(riverbed_lay1_targetidf,riverbed_lay1)
    imod.idf.write(riverbed_lay2_targetidf,riverbed_lay2)
    imod.idf.write(cond_lay1_targetidf,cond_lay1)
    imod.idf.write(cond_lay2_targetidf,cond_lay2)
    imod.idf.write(stage_targetidf,stage)

