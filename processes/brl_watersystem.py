# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2025 Deltares
#       Gerrit Hendriksen/Jarno Verkaik
#       gerrit.hendriksen@deltares.nl/jarno.verkaik@deltares.nl
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

# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/brl_modelling/processes/brl_watersystem.py $
# $Keywords: $

# system packages
import os
import json
import subprocess
import tempfile
from shutil import copyfile
import string
import time
from random import choice, randint
from unittest import result
import copy
from collections import defaultdict

# conda packages
import rasterio
import xarray
import geojson

# third party
import imod
import xarray as xr

import logging
LOGGER= logging.getLogger("PYWPS")


# local scripts
from processes.brl_utils import write_output, read_config, loguseractivity
from processes.brl_utils_vector import createpointer, createmodelextent_multiple, definetotalextent_from_polylist, transformpolygon
from processes.brl_utils_geoserver import load2geoserver, handleoutput


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


def setupModelRUNscenario(modeltmpdir, modelextent, template_run):
    # Read template
    print("template scenariorunfile exists:", os.path.isfile(template_run))
    # template_run = r"D:\projecten\datamanagement\rws\BasisRivierbodemLigging\wps_brl_modelling\model\nhi_template_nt.run"
    with open(template_run, "r") as myfile:
        data = myfile.read()
    print("modelextent:", modelextent)
    modeltmpdirw=modeltmpdir.replace('/','\\')
    print("modeltmpdirw", modeltmpdirw)
    #data = data.format(outputfolder=modeltmpdir,
    data = data.format(
        x0=str(modelextent[0][0]),
        y0=str(modelextent[0][1]),
        x1=str(modelextent[1][0]),
        y1=str(modelextent[1][1]),
        f=modeltmpdirw,
    )

    # Write run file
    runfile = os.path.join(modeltmpdir, "imod.run")
    print("runfile for scenario calculation: ", runfile)
    with open(runfile, "w") as runf:
        runf.write("%s" % data)
    return runfile


def setupModelRUNscenario_generic(modeltmpdir, modelextent, template_run, rfDict):
    # Read template

    # template_run = r"D:\projecten\datamanagement\rws\BasisRivierbodemLigging\wps_brl_modelling\model\nhi_template_nt.run"
    with open(template_run, "r") as myfile:
        data = myfile.read()
    modeltmpdirw=modeltmpdir.replace('/','\\')
    data = data.format(outputfolder=modeltmpdirw,
    #data = data.format(
        x0=str(modelextent[0][0]),
        y0=str(modelextent[0][1]),
        x1=str(modelextent[1][0]),
        y1=str(modelextent[1][1]),
        rivcond="\n".join(rfDict['cond']),
        rivstage="\n".join(rfDict['stage']),
        rivboth="\n".join(rfDict['rbot']),
        rivinf="\n".join(rfDict['inf']),
    )

    # Write run file
    runfile = os.path.join(modeltmpdir, "imod.run")
    print("runfile for scenario calculation: ", runfile)
    with open(runfile, "w") as runf:
        runf.write("%s" % data)
    return runfile


def setupModelRUNReferentie(modeltmpdir, modelextent, template_run, outres):
    # Read template
    with open(template_run, "r") as myfile:
        data = myfile.read()

    # Override configuration (point + margin)
    # data = data.format(outputfolder=modeltmpdir,
    print("brl_utils_imod - setupModelRUNReferentie", modelextent)
    data = data.format(
        outputfolder=modeltmpdir,
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


def adjustrivpackage_generic(cf, extent, measDict, modeltmpdir, modeldir, tmpdir, outres):
    ppref = '***** ' + adjustrivpackage_generic.__name__
    apply_resis = True

    # flag for consistency check/modification
    riv_consistent = bool(cf.get('Model','riv_consistent'))
    print(f'{ppref}: riv_consistent = {riv_consistent}')
 
    hsys1 = 'h_'
    rsList = ['p','s','t','h1','h2']
    # note: rvar and scvar should be matching!
    rvar   = ['cond',     'stage',     'rbot',     'inf']
    if apply_resis:
        fvar   = [outres*outres, None, None, None]
        scvar  = ['resisDiff', 'stageDiff', 'rbotDiff', 'infDiff']
    else:
        fvar   = [None, None, None, None]
        scvar  = ['condDiff', 'stageDiff', 'rbotDiff', 'infDiff']

    # number of polygons/areas
    npoly = len(measDict)

    mDict = copy.deepcopy(measDict)
    for ipoly in range(npoly):
        for key in measDict[ipoly].keys():
            if hsys1 in key:
                for hsys2 in ['h1_','h2_']:
                    new_key = hsys2+key.split(hsys1)[1]
                    mDict[ipoly][new_key] = measDict[ipoly][key]

    rivDict = {}; rivdatDict = {}
    for rs in rsList:
        rivdatDict[rs] = {}
        try:
            rivDict[rs] = eval(cf.get('Model',f'riv{rs}'))
        except:
            raise Exception(f'{ppref}: could not read {rs} from config file.')
        for rv in rvar:
            rivDict[rs][f'local_{rv}'] = None
            rivdatDict[rs]['active'] = False
            rivdatDict[rs][rv] = {'active': False, 'active_ipoly': {}, 'dat': None, 'pointer_ipoly': {}}
        
    # check the active river
    for rs in rsList:
        ivar = 0
        for rv in rvar:
            rvd = rs + '_' + scvar[ivar]; ivar += 1
            # loop over the area(s)
            for ipoly in range(npoly):
                try:
                    v = float(mDict[ipoly][rvd])
                except:
                    continue
                if (abs(v) > 0.):
                    rivdatDict[rs]['active'] = True
                    rivdatDict[rs][rv]['active'] = True
                    rivdatDict[rs][rv]['active_ipoly'][ipoly] = True
                else:
                    rivdatDict[rs][rv]['active_ipoly'][ipoly] = False

    # loop over the river systems       
    for rs in rsList:
        if not rivdatDict[rs]['active']:
            continue 

        print(f'{ppref}: processing river system "{rs}"')
        ivar = 0
        # loop over the river variables
        for rv in rvar:
            if not rivdatDict[rs][rv]['active']:
                ivar += 1
                continue
    
            rvd = rs + '_' + scvar[ivar]
            fv = fvar[ivar]
            ivar += 1
            print(f'{ppref}: processing for variable "{rv}/{rvd}"')

            f = os.path.join(modeldir,rivDict[rs]['subdir'],rivDict[rs][rv])
            print(f'{ppref}: reading {f}')
            try:
                rivdatDict[rs][rv]['dat'] = imod.idf.open(f).squeeze("layer", drop=True) 
            except:
                rivdatDict[rs][rv]['dat'] = imod.idf.open(f)

            # set pointer extent
            ext = imod.util.spatial_reference(rivdatDict[rs][rv]['dat'])
            extent_pointer = [(ext[1], ext[2]),(ext[4],ext[5])]
            cs_pointer = ext[0]

            # loop over the area(s)
            for ipoly in range(npoly):
                if (rivdatDict[rs][rv]['active_ipoly'][ipoly]):              
                    poly = measDict[ipoly]['polygon']
                    rivdatDict[rs][rv]['pointer_ipoly'][ipoly] = createpointer(poly, extent_pointer, cs_pointer)
                    pointer = rivdatDict[rs][rv]['pointer_ipoly'][ipoly]
                    v = float(mDict[ipoly][rvd])
                    if (fv is not None):
                        v = fv / v
                    rivdatDict[rs][rv]['dat'] = xr.where(pointer.notnull(), rivdatDict[rs][rv]['dat'] + v, 
                                                         rivdatDict[rs][rv]['dat'])

        # consistent checks
        if riv_consistent:
            rv1, rv2, rv3, rv4 = rvar
            # Conductance:
            if rivdatDict[rs][rv1]['active']:
                for ipoly in range(npoly):
                    if (rivdatDict[rs][rv1]['active_ipoly'][ipoly]):              
                        pointer = rivdatDict[rs][rv1]['pointer_ipoly'][ipoly]
                        # Set positive conductance!
                        rivdatDict[rs][rv1]['dat'] = xr.where((rivdatDict[rs][rv1]['dat'] < 0.) & 
                                                              (pointer.notnull()), 0., rivdatDict[rs][rv1]['dat'])
            # Stage:
            if rivdatDict[rs][rv2]['active']:
                if not rivdatDict[rs][rv3]['active']: # get bottom               
                    f = os.path.join(modeldir,rivDict[rs]['subdir'],rivDict[rs][rv3])
                    print(f'{ppref}: reading for system "{rs}" variable "{rv3}": {f}')
                    try:
                        xrv = imod.idf.open(f).squeeze("layer", drop=True)
                    except:
                        xrv = imod.idf.open(f)
                else:
                    xrv = rivdatDict[rs][rv3]['dat'] 

                for ipoly in range(npoly):
                    if (rivdatDict[rs][rv2]['active_ipoly'][ipoly]):              
                        pointer = rivdatDict[rs][rv2]['pointer_ipoly'][ipoly]
                        # When the stage is below the bottom, set the stage equal to the bottom
                        rivdatDict[rs][rv2]['dat'] = xr.where((rivdatDict[rs][rv2]['dat'] < xrv) & 
                                                              (pointer.notnull()), xrv, rivdatDict[rs][rv2]['dat'])
            # Bottom:
            if rivdatDict[rs][rv3]['active']:
                if not rivdatDict[rs][rv2]['active']: # get stage               
                    f = os.path.join(modeldir,rivDict[rs]['subdir'],rivDict[rs][rv2])
                    print(f'{ppref}: reading for system "{rs}" variable "{rv2}": {f}')
                    try:
                        xrv = imod.idf.open(f).squeeze("layer", drop=True)
                    except:
                        xrv = imod.idf.open(f)
                else:
                    xrv = rivdatDict[rs][rv2]['dat']

                for ipoly in range(npoly):
                    if (rivdatDict[rs][rv3]['active_ipoly'][ipoly]):              
                        pointer = rivdatDict[rs][rv3]['pointer_ipoly'][ipoly]
                        # When the bottom is above the stage, set the bottom equal to the stage
                        rivdatDict[rs][rv3]['dat'] = xr.where((rivdatDict[rs][rv3]['dat'] > xrv) & 
                                                              (pointer.notnull()), xrv, rivdatDict[rs][rv3]['dat'])

        # write the results
        for rv in rvar:
            if rivdatDict[rs][rv]['active']:            
                f = os.path.join(modeltmpdir, rivDict[rs][rv])
                rivDict[rs][f'local_{rv}'] = f
                print(f'{ppref}: writing for system "{rs}" variable "{rv}": {f}')
                imod.idf.write(f, rivdatDict[rs][rv]['dat'])         

    # set the file names to be used in the runfile
    for rs in rsList:
        for rv in rvar:
            if rivDict[rs][f'local_{rv}'] != None:
                rivDict[rs][rv] = rivDict[rs][f'local_{rv}']
            else:
                rivDict[rs][rv] = os.path.join(modeldir,rivDict[rs]['subdir'],rivDict[rs][rv])

    # set the dictonary used for writing the scenarion runfile
    rfDict = {}
    for rv in rvar:
        rfDict[rv] = []
        for rs in rsList:
            ilay = rivDict[rs]['layer']
            f = rivDict[rs][rv]
            s = f'{ilay},1,0,{f}'
            rfDict[rv].append(s)

    return rfDict

def setupgwmodelandrun(cf, extent, measDict, outres, scen0):
    tmpdir = cf.get("wps", "tmp")
    rfPref = 'nhi_scenario_watersystem'
   
    # get the directory from the config file where the template is stored
    modeldir = cf.get("Model", "modeldir")
    if os.name == "nt":
        if scen0:
            template_run = os.path.join(modeldir, "nhi_referentie_nt.run")
            print('reference runfile', template_run)
        else:
            template_run = os.path.join(modeldir, f"{rfPref}_nt.run")
            print('scenario runfile',template_run)
    else:
        if scen0:
            template_run = os.path.join(modeldir, "nhi_referentie.run")
        else:
            template_run = os.path.join(modeldir, f"{rfPref}.run")

    # make new temp dir where runfile and modeloutput is stored
    modeltmpdir = mkTempDir(tmpdir)

    # modeltmpdir = r'C:\Users\hendrik_gt\AppData\Local\Temp\tmp4p112xlp'
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
        print("brl_utils_imod - preparing scen0")
        runfile = setupModelRUNReferentie(modeltmpdir, extent, template_run, outres)
    else:
        print("brl_utils_imod - preparing scenario run")
        print(modeltmpdir, modeldir, tmpdir)
        # Adapt inputfiles based on scenario
        rfDict = adjustrivpackage_generic(cf, extent, measDict, modeltmpdir, modeldir, tmpdir, outres)
        # create scen runfile
        print(modeltmpdir, extent, template_run)
        runfile = setupModelRUNscenario_generic(modeltmpdir, extent, template_run, rfDict)

    # run the model with the copied exe
    runModel(exe, runfile)
    return modeltmpdir


def mainHandler(json_string):
    """
    successor of brl_utils_imod, there's no waters id anymore, but geojson incl. measures
    """
    
    # call loguseractivity
    loguseractivity('process watersystems')

    # Read configuration
    cf = read_config()

    # read the json string
    areajson = geojson.loads(json_string)
    
    # reproject polygon to 28992 and determine the extent
    polyList = transformpolygon(json_string, "EPSG:4326", "EPSG:28992")
    buf = float(cf.get("Model", "buffer"))
    outres = 250.
    extent = definetotalextent_from_polylist(polyList, buf, outres)    

    # Create the dictionaries with measures
    measDict = {}; measDictMap = {}
    npoly = len(areajson["features"])
    for ipoly in range(npoly):
        dct = areajson['features'][ipoly]['properties']
        dct['polygon'] = polyList[ipoly]
        dct['outres'] = outres
        measDict[ipoly] = dct

    try:
        #pass
        refruntmpdir = setupgwmodelandrun(cf, extent, measDict, outres, True) # reference
    except Exception as e:
        print("Error during calculation model reference!:", e)
    try:
        #pass
        scenruntmpdir = setupgwmodelandrun(cf, extent, measDict, outres, False) # scenario
    except Exception as e:
        print("Error during calculation model scenario!:", e)
    # # calculate the difference map, convert to GTIFF and load into geoserver
    # # bear in mind, this should be done for all layers
    resultpath = cf.get("GeoServer", "resultpath")
    baseUrl = cf.get("GeoServer", "wms_url")
    nlayers = int(cf.get("Model", "nlayers"))
    try:
        dctresults = handleoutput(nlayers, scenruntmpdir, refruntmpdir, scenruntmpdir)
        res_dict = defaultdict(list)
        for output in dctresults.keys():
            res = []
            lstresults = dctresults[output][0]
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
                res_dict[subfolder].append({
                    "name": f"{folder} {wmsname} laag {l}",
                    "layer": wmslayers[ilay],
                    "url": baseUrl,
                })
            # Now convert to desired output format:
            res = [{"folder": folder, "contents": items} for folder, items in res_dict.items()]            
    except Exception as e:
        print("Error during calculation of differences and uploading tif!:", e)
        res = None
    return json.dumps(res)