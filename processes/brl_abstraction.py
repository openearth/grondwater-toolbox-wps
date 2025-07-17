# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2025 Deltares
#       Gerrit Hendriksen
#       Jarno Verkaik
#       gerrit.hendriksen@deltares.nl
#       jarno.verkaik@deltares.nl
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

# $HeadURL: https://svn.oss.deltares.nl/repos/openearthtools/trunk/python/applications/wps/brl_modelling/processes/brl_utils_geoserver.py $
# $Keywords: $

# system pacakages
# from builtins import anext
import os
import json
from pyexpat.errors import XML_ERROR_DUPLICATE_ATTRIBUTE
from turtle import shapetransform
import geojson
import subprocess
from shapely.geometry import shape, Point
import tempfile
from shutil import copyfile
import string
import time
from random import choice, randint
from collections import defaultdict

# conda packages
import rasterio
import xarray

# third party
import imod

import logging
LOGGER= logging.getLogger("PYWPS")

# local scripts (abbrieviation used to be from processes.brl_utils import!)
from processes.brl_utils import write_output, read_config, loguseractivity
from processes.brl_utils_vector import roundCoords, transformpointcoords
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


def setupModelRUNscenario(modeltmpdir, modelextent, template_run, nwel, anipf, ilay, outres):
    # Read template
    print('in setupmodel run scenario',str(outres))
    with open(template_run, "r") as myfile:
        data = myfile.read()

    # it seems that anipf has the wrong formatting for iMODFLOW, but since the ipf is copied into the work folder,
    # replace the path by \
    anipf = os.path.join(""".\\""", os.path.basename(anipf))
    # Override configuration (point + margin)
    # data = data.format(outputfolder=modeltmpdir,
    print("template read")
    data = data.format(
        outputfolder=modeltmpdir,
        outres = str(outres),
        x0=str(modelextent[0][0]),
        y0=str(modelextent[0][1]),
        x1=str(modelextent[1][0]),
        y1=str(modelextent[1][1]),
        l=str(ilay),
        n=str(nwel),
        anipf=anipf,
    )

    # Write run file
    runfile = os.path.join(modeltmpdir, "imod.run")
    print("runfile for scenario calculation: ", runfile)
    with open(runfile, "w") as runf:
        runf.write("%s" % data)
    return runfile


def setupModelRUNReferentie(modeltmpdir, modelextent, template_run, outres):
    """creates a runfile for a reference run (so, no scenario)

    Args:
        modeltmpdir (string): string to path where reference run is carried out
        modelextent (list): list of list of points
        template_run (string): string with path to template runfile

    Returns:
        string: string of the path to the filled runfile
    """
    print("template reference runfile exists:", os.path.isfile(template_run))
    # Read template
    with open(template_run, "r") as myfile:
        data = myfile.read()

    # Override configuration (point + margin)
    # data = data.format(outputfolder=modeltmpdir,
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

def setupgwmodelandrun(cf, modeltmpdir, extent, outres, ipf=None, ilay=None):
    # extent = 5000
    # r"C:\Users\hendrik_gt\AppData\Local\Temp\waters_1573655087489443_extent_rd.geojson"
    # in the tmpdir (is the os tempdir) temp files are stored. Based on the watersId a couple of files are stored
    # tmpdir = gettmpdir()
    # tmpdir = cf.get('wps', 'tmp')

    # get the directory from the config file where the template is stored
    modeldir = cf.get("Model", "modeldir")
    if os.name == "nt":
        if ipf is not None:
            template_run = os.path.join(modeldir, "nhi_scenario_wells_nt.run")
            print("template_run", ipf)
        else:
            template_run = os.path.join(modeldir, "nhi_referentie_nt.run")
    else:
        if ipf is not None:
            template_run = os.path.join(modeldir, "nhi_scenario_wells.run")
        else:
            template_run = os.path.join(modeldir, "nhi_referentie.run")

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
    if ipf is not None:
        print("scenario ipf", ipf)
        nwel = int(cf.get("Model", "nwel"))
        runfile = setupModelRUNscenario(modeltmpdir, extent, template_run, nwel, ipf, ilay, outres)
    else:
        print(modeltmpdir, extent, template_run)
        # Adapt inputfiles based on scenario
        # adjustrivpackage(modeltmpdir, watersId, measures, modeldir, tmpdir)
        # create scen runfile
        runfile = setupModelRUNReferentie(modeltmpdir, extent, template_run,outres)
        print("referentierunfile", runfile)

    # run the model with the copied exe
    runModel(exe, runfile)


def createIPF(wdir, scenario):
    """createIPF creates additional abstraction well with for given point and layer

    Args:
        wdir (string): temporary directory where IPF is stored with given parameters
        scenario (list): list with xrd, yrd, layer, abstraction amount
    """
    xrd = scenario[0]
    yrd = scenario[1]
    ilay = scenario[2]
    dval = scenario[3]

    anipf = os.path.join(wdir, "well.ipf")
    with open(anipf, mode="w") as f:
        f.write("1" + "\n")
        f.write("4" + "\n")
        f.write("x" + "\n")
        f.write("y" + "\n")
        f.write("value" + "\n")
        f.write("laag" + "\n")
        f.write("0,txt" + "\n")
        f.write(" ".join([str(xrd), str(yrd), str(dval), str(ilay)]))
    f.close()
    return anipf


def mainHandler(point_json):
    """_summary_

    Args:
        point_json (_type_): _description_

    Returns:
        _type_: _description_
    """

    # call loguseractivity
    loguseractivity('process abstraction')
    
    # preparatory work
    cf = read_config()

    # point_json = '{"type": "FeatureCollection","name": "point","crs": 
    # { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
    # "features": [{ "type": "Feature", "properties": { "fid": 1, "layer": 3, "area": 5000, "abstraction" : 10000, "outres": 50 }, 
    # "geometry": { "type": "Point", "coordinates": [ 5.780, 52.145 ] } }]}'
    point_gjson = geojson.loads(point_json)

    # bear in mind, first reproject to 28992
    point = point_gjson["features"][0]["geometry"]
    aoi = point_gjson["features"][0]["properties"]["area"]
    ilay = point_gjson["features"][0]["properties"]["layer"]
    outres = point_gjson["features"][0]["properties"]["outres"]

    # bear in mind, users give an amount for abstraction, so abstraction is positive, but ... in the IPF it should be negatieve number
    # the unit is m3/day!
    dval = point_gjson["features"][0]["properties"]["abstraction"]
    if type(dval) == int or type(dval) == float:
        dval = dval * -1
    else:
        return "provide value for abstraction is not a number"

    # retrieve transformed point
    y, x = point["coordinates"]
    xrd, yrd = transformpointcoords(x, y)

    # create extent around this specific point
    anExtent = shape(Point(xrd, yrd)).buffer(aoi, cap_style=3)

    # convert the extent to modelextent
    xe0, ye0 = anExtent.bounds[0], anExtent.bounds[1]
    xe1, ye1 = anExtent.bounds[2], anExtent.bounds[3]
    theMExtent = [roundCoords(xe0, ye0, outres), roundCoords(xe1, ye1, outres)]

    # prepare modeltmpdir for the reference run
    reftmpdir = mkTempDir(cf.get("wps", "tmp"))
    try:
        setupgwmodelandrun(cf, reftmpdir, theMExtent, outres)
    except Exception as e:
        print("Error during calculation model reference!:", e)

    # prepare modeltmpdir for the scenario and create scenario ipf
    modeltmpdir = mkTempDir(cf.get("wps", "tmp"))
    anipf = createIPF(modeltmpdir, [xrd, yrd, ilay, dval])
    try:
        setupgwmodelandrun(cf, modeltmpdir, theMExtent, outres, anipf, ilay)
    except Exception as e:
        print("abs - Error during calculation model reference!:", e)

    # # # calculate the difference map, convert to GTIFF and load into geoserver
    # # bear in mind, this should be done for all layers
    resultpath = cf.get("GeoServer", "resultpath")
    baseUrl = cf.get("GeoServer", "wms_url")
    nlayers = int(cf.get("Model", "nlayers"))

    #try:
    dctresults = handleoutput(nlayers, modeltmpdir, reftmpdir, modeltmpdir,outres)
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
        
            if 'ref' in wmslayers[ilay]:
                folder = 'referentie'
            elif 'dif' in wmslayers[ilay]:
                folder = 'verschil'
            elif 'scen' in wmslayers[ilay]:
                folder = 'scenario'
            else:
                folder = 'unknown'  # optional fallback
        
            res_dict[folder].append({
                "name": f"{folder} {wmsname} laag {l}",
                "layer": wmslayers[ilay],
                "url": baseUrl,
            })
        
        # Now convert to desired output format:
        res = [{"folder": folder, "contents": items} for folder, items in res_dict.items()]            
    #except Exception as e:
    #    print("Error during calculation of differences and uploading tif!:", e)
    #    res = None
    return json.dumps(res)
