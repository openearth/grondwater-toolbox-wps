# -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2019 Deltares
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
import rasterio
import xarray
from geoserver.catalog import Catalog
from geo.Geoserver import Geoserver

# third party
import imod

import logging
LOGGER= logging.getLogger("PYWPS")

def handleoutput(nlayers, scenruntmpdir, refruntmpdir, resultpath,outres=250):
    """Creates diffenrence rasters of the several outputfiles

    Args:
        scenruntmpdir (string): path to output of scenario calculation
        refruntmpdir (string): path to output of reference calculation
        resultpath (string): output path for the gtiffs

    Returns:
        _type_: _description_
    """

    dctdirs = {}
    dctdirs["head"] = ("grondwaterstand", "brl")
    dctdirs["bdgflf"] = ("flux onderkant", "kwel")

    print("refrtmpdir:", refruntmpdir)
    print("scentmpdir:", scenruntmpdir)
    print("resultpath:", resultpath)
    # check numbers of watersId
    anid = str(int(1000000 * time.time()))
    # from the tmpdir --> get head for layer of visualisation
    # create a difference raster based on the extent of the scenario vislayer
    dctresults = {}

    for dir in dctdirs.keys():
        print(dir)
        lstresults = []
        for i in range(1, nlayers + 1):
            head_ref = imod.idf.open(
                os.path.join(refruntmpdir, f"{dir}/{dir}_steady-state_l{i}.idf")
            ).squeeze("time")
            head_scen = imod.idf.open(
                os.path.join(scenruntmpdir, f"{dir}/{dir}_steady-state_l{i}.idf")
            ).squeeze("time")

            result = head_scen - head_ref
            if dir == 'bdgflf':
                result = 1000.0 * result / (outres * outres) # m3 --> mm
            result.attrs["crs"] = "epsg:28992"
            # this part cuts of 1 cell from the boundaries
            result.isel(x=slice(1, -1), y=slice(1, -1))
            resultgtif = os.path.join(
                resultpath,
                "".join(["diff{d}_{id}_l{l}.tif".format(d=dir, l=i, id=anid)]),
            )
            print("abs create output name", i, anid, resultgtif)
            fn = imod.rasterio.save(
                resultgtif, result, driver="GTIFF", pattern="{name}{extension}"
            )
            lstresults.append(resultgtif)
        dctresults[dir] = (lstresults, dctdirs[dir])
    return dctresults


def addsld(cf, gtifpath, workspace="temp", sld_style="brl"):
    layername = os.path.basename(gtifpath).replace(".tif", "")
    print("gtif layer", layername)
    cat = Catalog(
        cf.get("GeoServer", "rest_url"),
        username=cf.get("GeoServer", "user"),
        password=cf.get("GeoServer", "pass"),
    )

    # Associate SLD styling to it
    layer = cat.get_layer(layername)
    layer.default_style = cat.get_style(sld_style)
    cat.save(layer)
    cat.reload()


# function that is based on the latest geoserver rest package geoserver-rest
def load2geoserver(cf, lstgtif, sld_style="brl", aws="abs"):
    """Load gtif data into geoserver

    Args:
        cf (_type_): configparser object of the contents of a configuration file
        lstgtif (_type_): a list with gtif paths (incl. filenames)
        sld_style (str, optional): style name (shoul be there in geoserver) Defaults to 'brl'.
        aws (str, optional): Workspace, if give then will be created, otherwise defaults to 'abs'.

    Returns:
        _type_: wmslayer
    """
    # Initialize the library
    try:
        geo = Geoserver(
            cf.get("GeoServer", "rest_url").replace("/rest", ""),
            username=cf.get("GeoServer", "user"),
            password=cf.get("GeoServer", "pass"),
        )
    except:
        print("cannot connect to geoserver")
    geo.get_workspaces()
    try:
        ws = geo.get_workspace(workspace=aws)
        # For creating workspace
        if ws is None:
            ws = geo.create_workspace(workspace=aws)
        else:
            print(ws, "already exists")
    except:
        print("connection to workspace not set")

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
        print(lname, gtif)
        # For uploading raster data to the geoserver
        try:
            geo.create_coveragestore(layer_name=lname, path=gtif, workspace=aws)
            geo.publish_style(layer_name=lname, style_name=sld_style, workspace=aws)
            wmslay = aws + ":" + lname
            wmslayers.append(wmslay)
            print("coverage store created and style assigned for", lname)
            if lname.find('head') != -1:
                lname = lname+'cntrl'
                geo.create_coveragestore(layer_name=lname, path=gtif, workspace=aws)
                geo.publish_style(layer_name=lname, style_name='cntrln', workspace=aws)
                wmslay = aws + ":" + lname
                wmslayers.append(wmslay)
                print("coverage store created and style assigned ", lname)
        except:
            print("failed to create store for", lname)

        print(wmslay)
    print("de wms layers", wmslayers)
    return wmslayers

# Cleanup temporary layers and stores
def cleanup_temp(cf, workspace="temp"):
    # Connect and get workspace
    cat = Catalog(
        cf.get("GeoServer", "rest_url"),
        username=cf.get("GeoServer", "user"),
        password=cf.get("GeoServer", "pass"),
    )

    # Layers
    layers = cat.get_layers()
    for l in layers:
        if (workspace + ":") in l.name:
            print("Deleting layer = {}".format(l.name))
            try:
                cat.delete(l)
                print("OK")
            except:
                print("ERR")
    cat.reload()

    # Stores
    stores = cat.get_stores()
    print("-------------------")
    for s in stores:
        if workspace in s.workspace.name:
            print("Deleting store = {}".format(s.name))
            try:
                cat.delete(s)
                print("OK")
            except:
                print("ERR")
    cat.reload()
