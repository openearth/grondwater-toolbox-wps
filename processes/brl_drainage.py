# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2025 Deltares
#       Jarno Verkaik/Gerrit Hendriksen
#       jarno.verkaik@deltares.nl/gerrit.hendriksen@deltares.nl
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

# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/brl_modelling/processes/brl_drainage.py $
# $Keywords: $

# system pacakages
import os
import json
import subprocess
import tempfile
from shutil import copyfile
import string
import time
from random import choice, randint
from unittest import result
import numpy as np
import pandas as pd
import geopandas as gpd
from collections import defaultdict
# conda packages
import geojson
from shapely.geometry import shape, Polygon
import rasterio
import xarray as xr
# third party
import imod
import logging


# local scripts
from processes.brl_utils import write_output, read_config, loguseractivity
from processes.brl_utils_raster import rasterstats_qubic
from processes.brl_utils_vector import createpointer, createmodelextent_multiple, definetotalextent_from_polylist, transformpolygon
from processes.brl_utils_geoserver import load2geoserver, handleoutput

LOGGER= logging.getLogger("PYWPS")

def create_drn_input(modeltmpdir, measDict, measDictMap, modeldir, tmpdir, extent, outres):
    print('create_drn_input', modeltmpdir, measDict, measDictMap, modeldir, tmpdir, extent, outres)
    rfDict = {}
    rfDict["cond_lst"] = []
    rfDict["bodh_lst"] = []
    rfDict["conc_lst"] = []

    for ipoly in measDict.keys():
        poly = measDict[ipoly]['polygon']
        pointer = createpointer(poly, extent, outres)

        layer = measDict[ipoly][measDictMap['layer']]
        resis = measDict[ipoly][measDictMap['bodc']]
        both  = measDict[ipoly][measDictMap['bodh']]

        drn_cond_val = float(outres*outres) / float(resis)
        drn_both_val = float(both)

        drn_cond = xr.where(pointer.notnull(), drn_cond_val, np.nan)
        drn_both = xr.where(pointer.notnull(), drn_both_val, np.nan)

        f_drn_cond = f'sc_drn_cond_id{ipoly}_l{layer}.idf'         
        f_drn_both = f'sc_drn_both_id{ipoly}_l{layer}.idf'       

        imod.idf.write(os.path.join(modeltmpdir,f_drn_cond), drn_cond)
        imod.idf.write(os.path.join(modeltmpdir,f_drn_both), drn_both)

        f_drn_cond = os.path.join('.\\', f_drn_cond)     
        f_drn_both = os.path.join('.\\', f_drn_both) 

        rfDict["cond_lst"].append(f'{layer},1,0,{f_drn_cond}')
        rfDict["bodh_lst"].append(f'{layer},1,0,{f_drn_both}')
        rfDict["conc_lst"].append('1,1,0,0')

    return rfDict    

def createrandstring():
    allchar = string.ascii_letters
    randstr = "".join(choice(allchar) for x in range(randint(8, 14)))
    return randstr

def mkTempDir(tmpdir):
    # Temporary folder setup, because of permission issues this alternative has been created
    # modeldir=tempfile.mkdtemp()
    foldername = createrandstring().lower()
    modeltmpdir = os.path.join(tmpdir, foldername)
    os.makedirs(modeltmpdir)
    return modeltmpdir

def setupModelRUNscenario(modeltmpdir, rfDict, ndrn, modelextent, template_run, outres):
    # the new number of drains
    ndrn_new = ndrn + len(rfDict["cond_lst"])
    # Read template
    with open(template_run, "r") as myfile:
        data = myfile.read()
    if os.name == 'nt':
        modeltmpdir=modeltmpdir.replace('/','\\')
    data = data.format(outputfolder=modeltmpdir,
    #data = data.format(
        outres = str(outres),
        x0=str(modelextent[0][0]),
        y0=str(modelextent[0][1]),
        x1=str(modelextent[1][0]),
        y1=str(modelextent[1][1]),
        ndrn=str(ndrn_new),
        #drn_cond = '\n'.join([ str(acond) for acond in rfDict["cond_lst"] ]),
        #drn_both = '\n'.join([ str(abodh) for abodh in rfDict["bodh_lst"] ]),
        #drn_conc = '\n'.join([ str(aconc) for aconc in rfDict["conc_lst"] ]),
        drn_cond="\n".join(rfDict["cond_lst"]),
        drn_both="\n".join(rfDict["bodh_lst"]),
        drn_conc="\n".join(rfDict["conc_lst"]),
    )

    # Write run file
    runfile = os.path.join(modeltmpdir, "imod.run")
    with open(runfile, "w") as runf:
        runf.write("%s" % data)
    return runfile

def setupModelRUNReferentie(modeltmpdir, modelextent, template_run, outres):
    # Read template
    with open(template_run, "r") as myfile:
        data = myfile.read()

    # Override configuration (point + margin)
    # data = data.format(outputfolder=modeltmpdir,
    data = data.format( outputfolder=modeltmpdir,
        outres = str(outres),
        x0=str(modelextent[0][0]),
        y0=str(modelextent[0][1]),
        x1=str(modelextent[1][0]),
        y1=str(modelextent[1][1]),
    )

    # Write run file
    runfile = os.path.join(modeltmpdir, "imod.run")
    print("runfile: ", runfile)
    with open(runfile, "w") as runf:
        runf.write("%s" % data)
    return runfile


def runModel(exe, runfile):
    currentdir = os.getcwd()
    print("currentdir:", currentdir)
    if os.name != "nt":
        args = ["chmod", "+x", exe]
        subprocess.run(args)
    args = [os.path.join(exe), os.path.join(runfile)]
    print("args: ", args)
    os.chdir(os.path.dirname(exe))
    process = subprocess.run(args, shell=False, check=True)
    print("done:", process.returncode, process.stdout, process.stderr)
    os.chdir(currentdir)

def setupgwmodelandrun(cf, extent, measDict, measDictMap, outres, scen0):
    tmpdir = cf.get("wps", "tmp")

    # get the directory from the config file where the template is stored
    modeldir = cf.get("Model", "modeldir")

    if os.name == "nt":
        if scen0:
            template_run = os.path.join(modeldir, "nhi_referentie_nt.run")
            print('reference runfile', template_run)
        else:
            template_run = os.path.join(modeldir, "nhi_scenario_drains_nt.run")
            print('scenario runfile',template_run)
    else:
        if scen0:
            template_run = os.path.join(modeldir, "nhi_referentie.run")
        else:
            template_run = os.path.join(modeldir, "nhi_scenario_drains.run")

    # make new temp dir where runfile and modeloutput is stored
    modeltmpdir = mkTempDir(tmpdir)

    # to make sure imodflow creates output in the target dir, copy de exe and ibound_l1.idf to the modeltmpdir.
    lstfiles = [cf.get("Model", "exe"), "ibound_l1.idf", cf.get("Model", "license")]
    sp = os.path.dirname(lstfiles[0])
    # copy the exe to modeltmpdir
    exe = os.path.join(modeltmpdir, os.path.basename(lstfiles[0]))

    # in case testing on Windows OS, you need fmpich2.dll in de model.exe path
    lstdll = ["fmpich2.dll", "mpich2mpi.dll", "mpich2nemesis.dll", "netcdf.dll"]
    if os.name == "nt":
        for dll in lstdll:
            if os.path.isfile(os.path.join(sp, dll)):
                copyfile(os.path.join(sp, dll), os.path.join(modeltmpdir, dll))
            else:
                print("not able to copy ", dll)

    try:
        print("org exe path: ", cf.get("Model", "exe"))
        copyfile(lstfiles[0], exe)
        # copy ibound to modeltmpdir
        copyfile(os.path.join(sp, lstfiles[1]), os.path.join(modeltmpdir, lstfiles[1]))
        copyfile(os.path.join(sp, lstfiles[2]), os.path.join(modeltmpdir, lstfiles[2]))
    except Exception as e:
        print("Error with copying files!:", e)
    # the function setupModelRUN creates a runfile based on the given parameters, extent and factor of change
    if scen0:
        runfile = setupModelRUNReferentie(modeltmpdir, extent, template_run, outres)
    else:
        print(modeltmpdir, modeldir, tmpdir)
        # Adapt inputfiles based on scenario
        rfDict = create_drn_input(modeltmpdir, measDict, measDictMap, modeldir, tmpdir, extent, outres)
        # create scen runfile
        print(modeltmpdir, extent, template_run)
        ndrn = int(cf.get("Model", "ndrn"))
        runfile = setupModelRUNscenario(modeltmpdir, rfDict, ndrn, extent, template_run, outres)
    # run the model with the copied exe
    runModel(exe, runfile)
    return modeltmpdir

def mainHandler(json_string):
    # example json_string:
    # {"type": "FeatureCollection","name": "test_drainage","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },"features": [{ "type": "Feature", "properties": { "fid": 1, "id": 1, "layer": 1, "drn_res": 0.1, "drn_bodh": -1.0, "outres": 25, "buffer": 1000}, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.156277399770034, 52.176580968463142 ], [ 6.144994026135112, 52.172730059457152 ], [ 6.152601459519871, 52.165249248498547 ], [ 6.165923192478923, 52.169621072903709 ], [ 6.165923192478923, 52.169621072903709 ], [ 6.156277399770034, 52.176580968463142 ] ] ] } },{ "type": "Feature", "properties": { "fid": 2, "id": 2, "layer": 2, "drn_res": 0.01, "drn_bodh": -5.0, "outres": 25, "buffer": 1000}, "geometry": { "type": "Polygon", "coordinates": [ [ [ 6.163015019979431, 52.163635417180721 ], [ 6.155382824357055, 52.158334542860608 ], [ 6.159790787936715, 52.150517307127558 ], [ 6.170599714815764, 52.149613640671049 ], [ 6.17238649730023, 52.163276133533046 ], [ 6.17238649730023, 52.163276133533046 ], [ 6.163015019979431, 52.163635417180721 ] ] ] } }]}
    # Read configuration
    
    # call loguseractivity
    loguseractivity('process drainage')

    cf = read_config()

    # read the json string
    areajson = geojson.loads(json_string)

    # reproject polygon to 28992 and determine the extent
    polyList = transformpolygon(json_string, "EPSG:4326", "EPSG:28992")
    buf = float(cf.get("Model", "buffer"))
    outres = areajson['features'][0]['properties']['outres']
    extent = definetotalextent_from_polylist(polyList, buf, outres)

    # Create the dictionaries with measures
    measDict = {}; measDictMap = {}
    npoly = len(areajson["features"])
    for ipoly in range(npoly):
        dct = areajson['features'][ipoly]['properties']
        dct['polygon'] = polyList[ipoly]
        measDict[ipoly] = dct

    #                      |here as keys in json string
    measDictMap['layer'] = 'layer'
    measDictMap['bodc']  = 'drn_res'
    measDictMap['bodh']  = 'drn_bodh'

    # execute scenario 0 first, perhaps should be done in parallel process
    try:
        refruntmpdir = setupgwmodelandrun(cf, extent, measDict, measDictMap, outres, True)
    except Exception as e:
        print("Error during calculation model reference!:", e)
    try:
        scenruntmpdir = setupgwmodelandrun(cf, extent, measDict, measDictMap, outres, False)
    except Exception as e:
        print("Error during calculation model scenario!:", e)

    # calculate the difference map, convert to GTIFF and load into geoserver
    # bear in mind, this should be done for all layers
    resultpath = cf.get("GeoServer", "resultpath")
    baseUrl = cf.get("GeoServer", "wms_url")
    nlayers = int(cf.get("Model", "nlayers"))
    resstat = None

    try:
        dctresults = handleoutput(nlayers, scenruntmpdir, refruntmpdir, scenruntmpdir, outres)
        res_dict = defaultdict(lambda: defaultdict(list))
        for output in dctresults.keys():
            res = []
            lstresults = dctresults[output][0]
            
            # in case of differences in heads calculate total waterneed
            if output == 'head':
                wstatlayers = []
                for rlayer in lstresults:
                    if 'dif_head' in rlayer:
                        wstatlayers.append(rlayer)
                resstat = rasterstats_qubic(wstatlayers)
                print('resstat', resstat)

            wmslayers = load2geoserver(
                cf, lstresults
            )
            for ilay in range(len(wmslayers)):
                l = wmslayers[ilay].split('_')[3].replace('cntrl', '').replace('l', '')
                wmsname = dctresults[output][1][0]

                if 'cntrl' in wmslayers[ilay]:
                    wmsname = 'isolijnen'

                # set subfolder (i.e. head or flux, Grondwaterstand/Verticale stroming )
                if 'head' in wmslayers[ilay]:
                    subfolder = 'grondwaterstand'
                elif 'bdgflf' in wmslayers[ilay]:
                    subfolder = 'verticale stroming'

                # set folder names
                if 'ref' in wmslayers[ilay]:
                    folder = 'referentie'
                elif 'dif' in wmslayers[ilay]:
                    folder = 'verschil'
                elif 'scen' in wmslayers[ilay]:
                    folder = 'scenario'
                else:
                    folder = 'unknown'  # optional fallback
            
                #glue all together in dictionary with json notation
                res_dict[folder][subfolder].append({
                        "name": f"{folder} {wmsname} laag {l}",
                        "layer": wmslayers[ilay],
                        "url": baseUrl,
                    })

        # Convert to nested folder structure
        res = []
        for folder, subfolders in res_dict.items():
            contents = []
            for subfolder, items in subfolders.items():
                contents.append({
                    "folder": subfolder,
                    "contents": items
                })
            res.append({
                "folder": folder,
                "contents": contents
        })
        # set the additional output waterstat 
        # --> watervraag (cumulatief verschil van verschil in waterstanden)
        # --> amount of water availabl/desired (cumulative sum of differences in waterstages)
        response = {"layers": res, "waterstat":resstat}
    except Exception as e:
        print("Error during calculation of differences and uploading tif!:", e)
        response = None
    return json.dumps(response)


def deprecated():
    try:
        dctresults = handleoutput(nlayers, scenruntmpdir, refruntmpdir, scenruntmpdir)
        res_dict = defaultdict(list)
        for output in dctresults.keys():
            res = []
            lstresults = dctresults[output][0]
            # in case of differences in heads calculate total waterneed
            wstatlayers = []
            for output in lstresults:
                if 'dif_head' in output:
                    wstatlayers.append(output)
            print('wstatlayers', wstatlayers)
            resstat = rasterstats_qubic(lstresults)

            # load all layers in geoserver
            wmslayers = load2geoserver(
                cf, lstresults
            )

            # setup json file with all layers in the correct folders and subfolders
            for ilay in range(len(wmslayers)):
                l = wmslayers[ilay].split('_')[3].replace('cntrl', '').replace('l', '')
                wmsname = dctresults[output][1][0]

                if 'cntrl' in wmslayers[ilay]:
                    wmsname = 'isolijnen'

                # set subfolder (i.e. head or flux, Grondwaterstand/Verticale stroming )
                if 'head' in wmslayers[ilay]:
                    subfolder = 'grondwaterstand'
                elif 'bdgflf' in wmslayers[ilay]:
                    subfolder = 'verticale stroming'

                # set folder names
                if 'ref' in wmslayers[ilay]:
                    folder = 'referentie'
                elif 'dif' in wmslayers[ilay]:
                    folder = 'verschil'
                elif 'scen' in wmslayers[ilay]:
                    folder = 'scenario'
                else:
                    folder = 'unknown'  # optional fallback
            
                #glue all together in dictionary with json notation
                res_dict[subfolder].append({
                    "name": f"{folder} {wmsname} laag {l}",
                    "layer": wmslayers[ilay],
                    "url": baseUrl,
                })

            # Now convert to desired output format:
            res = [{"folder": folder, "contents": items} for folder, items in res_dict.items()]
            print('resstat 2', resstat)            
            res['waterstat'] = resstat
    except Exception as e:
        print("Error during calculation of differences and uploading tif!:", e)
        res = None
    return json.dumps(res)
