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

import os
import time

# conda packages

from geo.Geoserver import Geoserver, GeoserverException


# third party
import imod

import logging
LOGGER= logging.getLogger("PYWPS")

def creategtif(i, uid, imodobj, fdir, mtype, prefix, outres=250):
    """Function creates geotif in the given path returns complete path setting. In case of mtype bdgflf it converts the data to mm

    Args:
        i (int)              : layernumber
        uid (int)            : unique identifier
        imodobj (xarray obj) : the xarray object build from iMODF IDF files
        fdir (string)        : output file dir
        mtype (string)       : indication for type of input file, i.e. head or bdgflf (this should be similar to iMODFLOW setup)
        prefix (string)      : for now this is a string indicating the scenario type, i.e. ref (reference), scen (scenario) and dif (difference)
        outres (int)         : defaults to default raster size of model (250 m), but can be reciproke equivalent of 250

    returns:
        resultgtif (string)  : full pathname and filename of the resulting GeoTIFF            
    """
    # this part cuts of 1 cell from the boundaries
    imodobj.isel(x=slice(1, -1), y=slice(1, -1))
    
    if mtype == 'bdgflf': 
        # for bdgflf conversion from m3 to mm following is required
        imodobj = 1000.0 * imodobj / (outres * outres) # m3 --> mm

    # assign proper epscode
    imodobj.attrs["crs"] = "epsg:28992"

    resultgtif = os.path.join(
        fdir,
        "".join(["{pf}_{d}_{id}_l{l}.tif".format(pf=prefix,d=mtype, id=uid, l=i)]),
    )        
    print('creategtif', resultgtif)
    imod.rasterio.save(
        resultgtif, imodobj, driver="GTIFF", pattern="{name}{extension}"
    )
    logging.info("abs create output name", i, uid, resultgtif)
    return os.path.normpath(resultgtif)


def handleoutput(nlayers, scenruntmpdir, refruntmpdir, resultpath,outres=250):
    """Creates diffenrence rasters of the several outputfiles

    Args:
        nlayers (inte): number of modellayers
        scenruntmpdir (string): path to output of scenario calculation
        refruntmpdir (string): path to output of reference calculation
        resultpath (string): output path for the gtiffs
        outres (int): defaults to default raster size of model (250 m), but can be reciproke equivalent of 250
    Returns:
        dictresults: per mtype (model data type, i.e. head, bdgflf) list of results for heads, fluxes and differences
    """
    # dictionary that stores information on generated tifs (incl. paths) and styles
    dctmtype = {}
    dctmtype["head"] = ("grondwaterstand", "brl")
    dctmtype["bdgflf"] = ("flux onderkant", "kwel")

    logging.info("refrtmpdir:", refruntmpdir)
    logging.info("scentmpdir:", scenruntmpdir)
    logging.info("resultpath:", resultpath)

    # create Unique ID for this session
    uid = str(int(1000000 * time.time()))
 
    # from the tmpdir --> get head for layer of visualisation
    # create a difference raster based on the extent of the scenario vislayer
    dctresults = {}

    for mtype in dctmtype.keys():
        lstresults = []
        for i in range(1, nlayers + 1):
            #print('handleoutput', mtype, i)
            if mtype == 'head':
                # reference situation --- process head 
                head_ref = imod.idf.open(
                    os.path.join(refruntmpdir, f"{mtype}/{mtype}_steady-state_l{i}.idf")
                ).squeeze("time")
                #).groupby("time",squeeze=False)

                #print('handleoutput', os.path.join(refruntmpdir, f"{mtype}/{mtype}_steady-state_l{i}.idf"))
                resultgtif = creategtif(i,uid,head_ref, refruntmpdir, mtype,'ref')
                lstresults.append(resultgtif)

                # scenario situation --- process head 
                head_scen = imod.idf.open(
                    os.path.join(scenruntmpdir, f"{mtype}/{mtype}_steady-state_l{i}.idf")
                ).squeeze("time")
                resultgtif = creategtif(i,uid,head_scen, scenruntmpdir,mtype, 'scen')
                lstresults.append(resultgtif)

                # process the difference between head in scenarion and reference situation
                result = head_scen - head_ref
                resultgtif = creategtif(i,uid, result, resultpath, mtype, 'dif')
                lstresults.append(resultgtif)
            elif mtype == 'bdgflf':
                # reference situation --- process bdgflf 
                flf_ref = imod.idf.open(
                    os.path.join(refruntmpdir, f"{mtype}/{mtype}_steady-state_l{i}.idf")
                ).squeeze("time")
                resultgtif = creategtif(i,uid,flf_ref, refruntmpdir,mtype,'ref',outres)
                lstresults.append(resultgtif)

                # scenario situation --- process bdgflf
                flf_scen = imod.idf.open(
                    os.path.join(scenruntmpdir, f"{mtype}/{mtype}_steady-state_l{i}.idf")
                ).squeeze("time")
                resultgtif = creategtif(i,uid,flf_scen, scenruntmpdir,mtype,'scen', outres)
                lstresults.append(resultgtif)

                # process the difference between bdgflf in scenarion and reference situation
                result = flf_scen - flf_ref
                resultgtif = creategtif(i,uid, result, resultpath, mtype,'dif', outres)
                lstresults.append(resultgtif)
        dctresults[mtype] = (lstresults, dctmtype[mtype])
    return dctresults


# function that is based on the latest geoserver rest package geoserver-rest
def load2geoserver(cf, lstgtif, sld_style="brl", aws="abs"):
    """Load gtif data into geoserver

    Args:
        cf (configparser obj)    : configparser object of the contents of a configuration file
        lstgtif (list)           : a list with gtif paths (incl. filenames)
        sld_style (str, optional): style name (shoul be there in geoserver) Defaults to 'brl'.
        aws (str, optional)      : Workspace, if give then will be created, otherwise defaults to 'abs'.

    Returns:
        List                     : of wmslayers
    """

    dctstyles = {}
    dctstyles['ref_head']    = ("grondwaterstand referentie",'maaiveld_tov_nap')
    dctstyles['scen_head']   = ("grondwaterstand scenario",'maaiveld_tov_nap')
    dctstyles['cntrl']       = ("contourlijnen grondwaterstand",'cntrln_ac')
    dctstyles['ref_bdgflf']  = ("verticale flux referentie",'kwel')
    dctstyles['scen_bdgflf'] = ("verticale flux scenario",'kwel')
    dctstyles['dif_head']    = ("verschil grondwaterstand",'brl')
    dctstyles['dif_bdgflf']  = ("verschil verticale flux",'kwel_mmd_2')
    dctstyles['dif_cntrl']   = ("contourlijnen verschilsituati",'cntrl')


    # Initialize the library
    try:
        geo = Geoserver(
            cf.get("GeoServer", "rest_url").replace("/rest", ""),
            username=cf.get("GeoServer", "user"),
            password=cf.get("GeoServer", "pass"),
        )
    except Exception as e:
        logging.info("unable to connect to geoserver", e)

    # fetch workspaces and check if workspace aws is already setup in if necessary create it
    geo.get_workspaces()
    try:
        ws = geo.get_workspace(workspace=aws)
        # For creating workspace
        if ws is None:
            ws = geo.create_workspace(workspace=aws)
        else:
            print(ws, "already exists")
    except GeoserverException as ge:
        logging('GeoserverException', ge)
        ws = geo.create_workspace(workspace=aws)
    except Exception as e:
        logging.info("other exception",e)

    # create emtpy list to harvest the wmslayers
    wmslayers = []

    for gtif in lstgtif:
        if aws == "brl":
            # lname = os.path.basename(gtif).replace(gtif.split('_')[-1],'').replace('_steady-state','')[:-1]
            lname = os.path.basename(gtif).replace(".tif", "")
        else:
            lname = (
                os.path.basename(gtif).replace(".tif", "").replace("_steady-state", "")
            )

        style_key = "_".join(lname.split('_')[:2])
        sld_style = dctstyles.get(style_key, [None])[1]
        logging.info('GTIF, set style for layer', os.path.normpath(gtif), lname,sld_style)
        #print('brl_utils_geoserver - gtifname', os.path.normpath(gtif))
        #print('brl_utils_geoserver - workspace', aws)
        #print('brl_utils_geoserver - style for layer', lname,sld_style)
        # For uploading raster data to the geoserver
        try:
            geo.create_coveragestore(layer_name=lname, path=os.path.normpath(gtif), workspace=aws)
            geo.publish_style(layer_name=lname, style_name=sld_style, workspace=aws)
            wmslay = f"{aws}:{lname}"
            wmslayers.append(wmslay)
            print(f"Coverage store created and style assigned for {lname}")
            if 'head' in lname:
                new_lname = f'{lname}cntrl'
                geo.create_coveragestore(layer_name=new_lname, path=os.path.normpath(gtif), workspace=aws)
                geo.publish_style(layer_name=new_lname, style_name='cntrln', workspace=aws)
                wmslay = f"{aws}:{new_lname}"
                wmslayers.append(wmslay)
                logging.info(f"Coverage store created and style assigned for {new_lname}")
        except Exception as e:
            logging.info(f"failed to create store for {lname},{str(e)}")

        print(wmslay)
    #print("de wms layers", wmslayers)
    return wmslayers


def cleanup_workspace_geoserver(rest_url, username, password, workspace):
    """
    Deletes all layers and coverage stores in a single workspace using geo.Geoserver.
    """
    geo = Geoserver(rest_url, username=username, password=password)

    print(f"Cleaning workspace: {workspace}")

    # Try to get and delete layers
    try:
        layers = geo.get_layers(workspace=workspace)["layers"]
        if not layers:
            print(f" → No layers returned for workspace '{workspace}' (may be empty or inaccessible).")
        else:
            for layer in layers["layer"]:
                lname = layer["name"]
                print(f" → Deleting layer: {lname}")
                geo.delete_layer(layer_name=lname, workspace=workspace)
    except Exception as e:
        print(f" ✖ Failed to retrieve or delete layers in workspace '{workspace}': {e}")

    # Try to get and delete coverage stores
    try:
        stores = geo.get_coveragestores(workspace=workspace)["coverageStores"]
        if not stores:
            print(f" → No coverage stores returned for workspace '{workspace}' (may be empty or inaccessible).")
        else:
            for store in stores["coverageStore"]:
                store_name = store["name"]
                print(f" → Deleting coverage store: {store_name}")
                geo.delete_coveragestore(coveragestore_name=store_name, workspace=workspace)
    except Exception as e:
        print(f" ✖ Failed to retrieve or delete coverage stores in workspace '{workspace}': {e}")



