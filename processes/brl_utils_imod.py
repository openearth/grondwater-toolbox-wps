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
import os
import json
import subprocess
import tempfile
from shutil import copyfile
import string
import time
from random import choice, randint
from unittest import result

# conda packages
import rasterio
import xarray

# third party
import imod

# local scripts
from processes.brl_utils import write_output
from processes.brl_utils import read_config
from processes.brl_utils_vector import createmodelextent, definetotalextent
from processes.brl_utils_geoserver import load2geoserver, handleoutput
from processes.brl_utils_prepareinput import adjustrivpackage

import logging
LOGGER= logging.getLogger("PYWPS")


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
    print("template scenariorunfile exists:", os.path.isfile(template_run))
    # template_run = r"D:\projecten\datamanagement\rws\BasisRivierbodemLigging\wps_brl_modelling\model\nhi_template_nt.run"
    with open(template_run, "r") as myfile:
        data = myfile.read()
    print("modelextent:", modelextent)
    modeltmpdirw=modeltmpdir.replace('/','\\')
    print("modeltmpdirw", modeltmpdirw)
    data = data.format(outputfolder=modeltmpdirw,
    #data = data.format(
        x0=str(modelextent[0][0]),
        y0=str(modelextent[0][1]),
        x1=str(modelextent[1][0]),
        y1=str(modelextent[1][1]),
        rivcond="\n".join(rfDict['cond']),
        rivstage="\n".join(rfDict['stage']),
        rivboth="\n".join(rfDict['both']),
        rivinf="\n".join(rfDict['inf']),
    )

    # Write run file
    runfile = os.path.join(modeltmpdir, "imod.run")
    print("runfile for scenario calculation: ", runfile)
    with open(runfile, "w") as runf:
        runf.write("%s" % data)
    return runfile


def setupModelRUNReferentie(modeltmpdir, modelextent, template_run):
    # Read template
    with open(template_run, "r") as myfile:
        data = myfile.read()

    # Override configuration (point + margin)
    # data = data.format(outputfolder=modeltmpdir,
    print("brl_utils_imod - setupModelRUNReferentie", modelextent)
    data = data.format(
        outputfolder=modeltmpdir,
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


def setupgwmodelandrun(cf, watersId, extent, measures, rivsys, scen0):
    # extent = 5000
    # r"C:\Users\hendrik_gt\AppData\Local\Temp\waters_1573655087489443_extent_rd.geojson"
    # in the tmpdir (is the os tempdir) temp files are stored. Based on the watersId a couple of files are stored
    # tmpdir = gettmpdir()
    tmpdir = cf.get("wps", "tmp")

    # backwards compatibility for 'hoofdsysteem'
    if rivsys != None:
        generic = True
        rfPref = 'nhi_scenario_generic'
    else:
        generic = False
        rfPref = 'nhi_scenario'
    # OVERRULE
    #generic = True
    #rfPref = 'nhi_scenario_generic'
   
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
        print("brl_utils_imod - prepartion scen0")
        runfile = setupModelRUNReferentie(modeltmpdir, extent, template_run)
    else:
        print("brl_utils_imod - prepartion scenario run")
        print("brl_utils_imod - ", type(measures))
        print(modeltmpdir, [watersId, measures], modeldir, tmpdir)
        # Adapt inputfiles based on scenario
        if not generic:
            adjustrivpackage(modeltmpdir, [watersId, measures], modeldir, tmpdir)
            # create scen runfile
            print(modeltmpdir, extent, template_run)
            runfile = setupModelRUNscenario(modeltmpdir, extent, template_run)
        else:
            rfDict = adjustrivpackage_generic(cf, modeltmpdir, [watersId, measures], rivsys, modeldir, tmpdir)
            # create scen runfile
            print(modeltmpdir, extent, template_run)
            runfile = setupModelRUNscenario_generic(modeltmpdir, extent, template_run, rfDict)

    # run the model with the copied exe
    runModel(exe, runfile)
    return modeltmpdir
    # obsolete part, first 0 scenario has to be run, then next. part below is move to main handler
    # the sc0dir is the directory which contains all input files and also a dir called def_scenario.
    # this is the initial run, based
    # sc0dir = os.path.join(modeldir,'def_scenario')
    # file = handleoutput(sc0dir, modeltmpdir,vislayer,watersId)
    # return file


def mainHandler(cf, measures, watersId, rivsys=None):
    if rivsys != None:
        # convert rivsys to a list
        rivsys = rivsys.split(',')
        if 'h' in rivsys:
            rivsys.remove('h')
            rivsys = ['h1','h2'] + rivsys

    # rip the config into pieces
    # bear in mind, that everypart can be a list, so configuration can be a list of jsons, from 2020
    # measures is a list of json strings
    # exept extent
    # for the 2020 version watersId is a list.
    print("in measures", measures)

    # function call to get the total extent of the model, in other words
    # all _extent_rd.geojson files are read and combined to 1 extent of the selected watercourses.
    extent = definetotalextent(cf, watersId)

    # measures = '{"id":"waters_1607097506779636","extent":"1000","calculationLayer":1,"riverbedDifference":"-10"},{"id":"waters_1607097511506478","extent":"1000","calculationLayer":1,"conductance":"10"},{"id":"waters_1607097506779637","extent":"1000","calculationLayer":1,"riverbedDifference":"-7"},{"id":"waters_1607097511506479","extent":"1000","calculationLayer":1,"conductance":"7"}'
    lstjsonmeasures = []
    for i in measures.split("},{"):
        lstjsonmeasures.append(
            json.loads("{" + i.replace("{", "").replace("}", "") + "}")
        )

    # execute scenario 0 first, perhaps should be done in parallel process
    try:
        refruntmpdir = setupgwmodelandrun(cf, watersId, extent, lstjsonmeasures, rivsys, True)
    except Exception as e:
        print("Error during calculation model reference!:", e)

    try:
        scenruntmpdir = setupgwmodelandrun(cf, watersId, extent, lstjsonmeasures, rivsys, False)
    except Exception as e:
        print("Error during calculation model scenario!:", e)

    # # calculate the difference map, convert to GTIFF and load into geoserver
    # # bear in mind, this should be done for all layers
    resultpath = cf.get("GeoServer", "resultpath")
    baseUrl = cf.get("GeoServer", "wms_url")
    nlayers = int(cf.get("Model", "nlayers"))
    print("imod_mh", resultpath, baseUrl)
    dctres = {}
    try:
        dctresults = handleoutput(nlayers, scenruntmpdir, refruntmpdir, scenruntmpdir)
        for output in dctresults.keys():
            res = []
            lstresults = dctresults[output][0]
            print(lstresults)
            wmslayers = load2geoserver(
                cf, lstresults, sld_style=dctresults[output][1][1]
            )
            
            for ilay in range(len(wmslayers)):
                l = wmslayers[ilay].split('_')[2].replace('cntrl','').replace('l','')
                wmsname = dctresults[output][1][0]
                if 'cntrl' in wmslayers[ilay]:
                    wmsname = 'isolijnen'
                res.append(
                    {
                        "name": f"verschil {wmsname} laag {l}",
                        "layer": "{lay}".format(lay=wmslayers[ilay]),
                        "url": "{b}".format(b=baseUrl),
                    }
                )
            dctres[output] = res
    except Exception as e:
        print("Error during calculation of differences and uploading tif!:", e)
        dctres = None
    return json.dumps(dctres)
    # res = []
    # try:
    #     lstresults = handleoutput(scenruntmpdir, refruntmpdir,watersId,resultpath)
    #     wmslayers = load2geoserver(cf,lstresults,aws='brl')
    #     for ilay in range(len(wmslayers)):
    #         l = ilay +1
    #         print(wmslayers[ilay])
    #         res.append({ "name": f"verschil grondwaterstand laag {l}",
    #                    "layer": "{lay}".format(lay=wmslayers[ilay]),
    #                    "url":"{b}".format(b=baseUrl)})
    # except Exception as e:
    #     print("Error during calculation of differences and uploading tif!:", e)
    #     layername='brl:head_steady-state_l'
    #     for l in range(1,8):
    #         res.append({ "name": f"verschil grondwaterstand laag {l}",
    #                    "layer": f"{layername}{l}",
    #                    "url":"{b}".format(b=baseUrl)})
    # return json.dumps(res)
