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
# from builtins import anextn
import os
import subprocess
from shutil import copyfile
import string
from random import choice, randint
import logging
import geojson
from collections import defaultdict
# conda packages

# local scripts (abbrieviation used to be from processes.brl_utils import!)
from processes.brl_utils import read_config, loguseractivity
from processes.brl_utils_vector import transformpolygon, createmodelextent
from processes.brl_utils_geoserver import load2geoserver, handleoutput
from processes.brl_utils_digit import deepenlake

LOGGER= logging.getLogger("PYWPS")
def createrandstring():
    """Create string with random charachters

    Returns:
        String: stringcomposed of random characters and integers
    """
    allchar = string.ascii_letters
    randstr = "".join(choice(allchar) for x in range(randint(8, 14)))
    return randstr


def mkTempDir(tmpdir):
    """Creates tmpdir on the filesystem (is OS independent)

    Args:
        tmpdir (String): string with base path

    Returns:
        String: path with modeldir composed of randomstring and number
    """
    # Temporary folder setup, because of permission issues this alternative has been created
    # modeldir=tempfile.mkdtemp()
    foldername = createrandstring().lower()
    modeltmpdir = os.path.join(tmpdir, foldername)
    os.makedirs(modeltmpdir)
    return modeltmpdir


def setupModelRUNscenario(modeltmpdir, modelextent, template_run, dirinputs, nwel, ilay):
    # Read template
    with open(template_run, "r") as myfile:
        data = myfile.read()

    if os.system != 'nt':
        dirinputs = dirinputs.replace('/','\\')

    # data = data.format(outputfolder=modeltmpdir,
    data = data.format(
        outputfolder=modeltmpdir,
        x0=str(modelextent[0][0]),
        y0=str(modelextent[0][1]),
        x1=str(modelextent[1][0]),
        y1=str(modelextent[1][1]),
        dirc=dirinputs,
        dirm=dirinputs,)
                        
    # Write run file
    runfile = os.path.join(modeltmpdir, "imod.run")

    with open(runfile, "w") as runf:
        runf.write("%s" % data)
    return runfile


def setupModelRUNReferentie(modeltmpdir, modelextent, template_run, outres=250):
    """creates a runfile for a reference run (so, no scenario)

    Args:
        modeltmpdir (string): string to path where reference run is carried out
        modelextent (list): list of list of points
        template_run (string): string with path to template runfile

    Returns:
        string: string of the path to the filled runfile
    """
    # Read template
    with open(template_run, "r") as myfile:
        data = myfile.read()

    # Override configuration (point + margin)
    # data = data.format(outputfolder=modeltmpdir,
    data = data.format(
        outputfolder=modeltmpdir,
        x0=str(modelextent[0][0]),
        y0=str(modelextent[0][1]),
        x1=str(modelextent[1][0]),
        y1=str(modelextent[1][1]),
        outres=str(outres),
    )

    # Write run file
    runfile = os.path.join(modeltmpdir, "imod.run")
    
    with open(runfile, "w") as runf:
        runf.write("%s" % data)
    return runfile


def runModel(exe, runfile):
    currentdir = os.getcwd()

    if os.name != "nt":
        args = ['chmod', '+x', exe]
        subprocess.run(args)

    args = [os.path.join(exe), os.path.join(runfile)]

    os.chdir(os.path.dirname(exe))
    process = subprocess.run(args, shell=False, check=True)
    os.chdir(currentdir)

def setupgwmodelandrun(cf, modeltmpdir, extent, scen, dirinputs=None, ilay=None):
    # in the tmpdir (is the os tempdir) temp files are stored. Based on the watersId a couple of files are stored
    # tmpdir = gettmpdir()
    # tmpdir = cf.get('wps', 'tmp')

    # get the directory from the config file where the template is stored
    modeldir = cf.get("Model", "modeldir")
    if os.name == "nt":
        if scen:
            template_run = os.path.join(modeldir, "nhi_scenario_digit_nt.run")
        else:
            template_run = os.path.join(modeldir, "nhi_referentie_nt.run")
    else:
        if scen:
            template_run = os.path.join(modeldir, "nhi_scenario_digit.run")
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
        copyfile(lstfiles[0], exe)
        # copy ibound to modeltmpdir
        copyfile(os.path.join(sp, lstfiles[1]), os.path.join(modeltmpdir, lstfiles[1]))
        copyfile(os.path.join(sp, lstfiles[2]), os.path.join(modeltmpdir, lstfiles[2]))
    except Exception as e:
        print("Error with copying files!:", e)
    # the function setupModelRUN creates a runfile based on the given parameters, extent and factor of change
    if scen:
        nwel = int(cf.get("Model", "nwel"))
        runfile = setupModelRUNscenario(
            modeltmpdir, extent, template_run, dirinputs, nwel, ilay)
    else:
        # Adapt inputfiles based on scenario
        # adjustrivpackage(modeltmpdir, watersId, measures, modeldir, tmpdir)
        # create scen runfile
        runfile = setupModelRUNReferentie(modeltmpdir, extent, template_run)


    # run the model with the copied exe
    runModel(exe, runfile)


def mainHandler(json_string):
    """Prepares all the input for the calculation of the effect of an dig exercise in primary system of waterways in the NL

    Args:
        json_string (string): Input from the wps part. Content should be:
        - geojson area
        - depth
        - layer
        -

    Returns:
        json: json representation of a dictionary with lists of layers per item (i.e. Groundwater heads, fluxes)
    """
    # call loguseractivity
    loguseractivity('process digit')

    # preparatory work

    cf = read_config()
    areajson = geojson.loads(json_string)
    
    # read the essentials
    polygon = areajson["features"][0]["geometry"]
    aoi = areajson["features"][0]["properties"]["area"]
    ilay = areajson["features"][0]["properties"]["layer"]
    depth = areajson["features"][0]["properties"]["depth"]

    # reproject polygon to 28992
    polyList = transformpolygon(json_string, "EPSG:4326", "EPSG:28992")
    tpoly = polyList[0]

    # derive bounds from polygon
    bnds = tpoly.bounds
    # create modelextent based on
    modelextent = createmodelextent(bnds, aoi)
    print('modelextent',str(modelextent))

    # prepare the reference model
    # prepare modeltmpdir for the reference run, make sure you use nhi_refenentie_nt.run
    reftmpdir = mkTempDir(cf.get("wps", "tmp"))
    try:
        setupgwmodelandrun(cf, reftmpdir, modelextent, False)
    except Exception as e:
        print("Error during calculation model reference!:", e)

    # prepare modeltmpdir for the scenario and create scenario
    # with the paths specified by deepenlake
    modeltmpdir = mkTempDir(cf.get("wps", "tmp"))
    dirinputs = deepenlake(cf, tpoly, depth, modeltmpdir)
    print('dirinputs',dirinputs)
    try:
        print('setupgwmodelandrun scenario modeltmpdir',modeltmpdir)
        setupgwmodelandrun(cf, modeltmpdir, modelextent, True, dirinputs, ilay)
    except Exception as e:
        print("abs - Error during calculation model reference!:", e)

    # # # calculate the difference map, convert to GTIFF and load into geoserver
    # # bear in mind, this should be done for all layers
    resultpath = cf.get("GeoServer", "resultpath")
    baseUrl = cf.get("GeoServer", "wms_url")
    nlayers = int(cf.get("Model", "nlayers"))

    try:
        dctresults = handleoutput(nlayers, modeltmpdir, reftmpdir, modeltmpdir)
        res_dict = defaultdict(lambda: defaultdict(list))
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
            #glue all together in dictionary with json notation
            res_dict[folder][subfolder].append({
                    "name": f"{folder} {wmsname} laag {l}",
                    "layer": wmslayers[ilay],
                    "url": baseUrl,
                })

        print(res_dict)
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
    except Exception as e:
        print("Error during calculation of differences and uploading tif!:", e)
        res = None
    return res
