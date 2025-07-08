 # -*- coding: utf-8 -*-
# Copyright notice
#   --------------------------------------------------------------------
#   Copyright (C) 2022 Deltares
#       Huite Bootsma
#       Gerrit Hendriksen
#       Jarno Verkaik
#       huite.bootsma@deltares.nl
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

"""
Main purpose is that data is converted into modelinput in specified directory.
Digit utils 'digs' data from the first layers. It is meant to be used in big lakes but ....
for now not restricted to that. Bear in mind, should be discussed with geohydrologists if this is
also applicable in terrestrial environments

"""

import os
from shapely.geometry.polygon import Polygon
import numpy as np
import imod
import xarray as xr
from pathlib import Path
import re

from processes.brl_utils import read_config

import logging
LOGGER= logging.getLogger("PYWPS")


# constants
ENTRY_RESISTANCE = 1.0 #day
K_AQUIFER = 1.0 #day

# def read_config():
#     import configparser
# 	# Default config file (relative path, does not work on production, weird)
#     if os.name == 'nt':
#         devpath = r'C:\svn'
#         confpath = os.path.join(devpath,'brl_configuration_local_brl.txt')
#     else:
#         confpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'brl_configuration.txt')
#     if not os.path.exists(confpath):
#         confpath = '/opt/pywps/processes/brl_configuration.txt'
# 	# Parse and load
#     cf = configparser.ConfigParser()
#     print(confpath)
#     cf.read(confpath)
#     return cf

def collapseLayers(da, method):
    da = da.copy()
    da["layer"] = (0.5 * (da["layer"] - 1)).astype(int) + 1
    if method == 'sum':
        da = da.groupby("layer").sum()
        return da.where(da>0)
    if method == 'min':
        da = da.groupby("layer").min()
        return da

def testing():
    from shapely.geometry.polygon import Polygon
    from shapely import wkt
    import geopandas as gpd
    import pandas as pd
    cf = read_config()
    depth = 17
    resultpath = 'a valid path'

    awktpoly = 'POLYGON ((157304.2025739554 527484.2884011992, 155862.7511919551 522583.1091179381, 158662.9405372438 518723.3688685104, 161005.1767597545 523329.2591359828, 161005.1767597545 523329.2591359828, 157304.2025739554 527484.2884011992))'
    polygon = wkt.loads(awktpoly)
    df = pd.DataFrame({'wkt':[polygon.to_wkt()]})
    gs = gpd.GeoSeries(polygon)
    gdf = gpd.GeoDataFrame(df,geometry=gs, crs="EPSG:28992")
    polygon = gdf

    deepenlake(cf, gdf, depth, resultpath)   #scenarios reference dir path

def shapefiletowkt(polygon):
    from shapely.geometry.polygon import Polygon
    from shapely import wkt 
    import geopandas as gpd
    import pandas as pd
    #polygon = wkt.loads(awktpoly)
    from shapely.wkt import dumps                  # check this change by Gerrit 13-12-2024

    #df = pd.DataFrame({'wkt':[polygon.to_wkt()]}) # check this change by Gerrit 13-12-2024
    df = pd.DataFrame({'wkt':[dumps(polygon)]})    # check this change by Gerrit 13-12-2024
    gs = gpd.GeoSeries(polygon)
    gdf = gpd.GeoDataFrame(df,geometry=gs, crs="EPSG:28992")
    return gdf


def deepenlake(cf, polygon, depth, resultpath):
    # get modellayers location from cf

    polygon = shapefiletowkt(polygon)

    basepath = cf.get('Model','modeldir')
    print(basepath)
    if os.path.isdir(basepath):
        pathtopbots = os.path.join(basepath,'lagenmodel')
    if not os.path.isdir(pathtopbots):
        return None
    else:
        print(pathtopbots)

    # collect tops and bots
    pattern = re.compile(r"(?P<name>[\w]+)_SDL(?P<layer>[\d+]*)_.*", re.IGNORECASE)
    top = imod.idf.open(pathtopbots+'/TOP_SDL*.IDF', pattern=pattern)
    bottom = imod.idf.open(pathtopbots+'/BOT_SDL*.IDF', pattern=pattern)

    c = imod.idf.open(os.path.join(basepath,'c/c*.idf'), pattern=r"{name}{layer}")
    #get bottom of the lake from the river package. We want the actual elevation of the bottom, ignoring layers. So we sum over all layers.
    #lake_bottom_3d = imod.idf.open(os.path.join(basepath,'riv/hoofdwater'+'/both_w_L*.IDF'), pattern='{name}_w_l{layer}') #both_w_l*.IDF' capital letter might result in errors
    lake_bottom_3d = imod.idf.open(os.path.join(basepath,'riv/hoofdwater'+'/both_w_l*.idf'), pattern='{name}_w_l{layer}') #both_w_l*.IDF' capital letter might result in errors
    lake_bottom = lake_bottom_3d.sum(dim="layer")

    # and bathmetry layer (AHN.idf) as bottom of the 0th SDL layer. In this way it is consistent with the rest of the layer model.
    # in one of the subsequent steps, we will use this as top of the first layer (=aquifer)
    bathymetry = imod.idf.open(pathtopbots+'/*AHN*.IDF').assign_coords(layer=0).expand_dims('layer')
    bottom = xr.concat([bottom, bathymetry], dim="layer").sortby("layer")
 
    # stuk om te plotten
    """
    da2d = top.sel(layer=1)
    da2d.plot.imshow()
    """

    # use the input polygon as a mask, convert the polygon to a mask raster
    pgoi = imod.prepare.rasterize(polygon, like=top.isel(layer=0))
    where = pgoi.notnull()
    #top = top.where(pgoi.notnull())
    #bottom = bottom.where(pgoi.notnull())
    #c = c.where(pgoi.notnull())
    lake_bottom = lake_bottom.where(pgoi.notnull())
    new_lake_bottom = lake_bottom - depth                  #depth of excavation

    """
Schets van het lagenmodel + bijbehorende bestandsnamen


~~~~~~~ wateroppervlak

_______ bodem van het meer
                   aquifer,   layer  1 --> top=AHN.IDF, bot=TOP_SLD1.pdf
####### SLD 1.idf, aquitard,  layer  2 --> top=TOP_SLD1.IDF, bot=BOT_SLD1.IDF
                   aquifer,   layer  3 --> top=BOT_SDL1.IDF, bot=TOP_SLD2.IDF
####### SLD 2.idf, aquitard,  layer  4 --> ...
                   aquifer,   layer  5 --> ...
####### SLD 3.idf, aquitard,  layer  6 --> ...
                   aquifer,   layer  7 --> ...
####### SLD 4.idf, aquitard,  layer  8 --> ...
                   aquifer,   layer  9 --> ...
####### SLD 5.idf, aquitard,  layer 10 --> ...
                   aquifer,   layer 11 --> top=BOT_SDL5.IDF, bot=TOP_SLD6.IDF
####### SLD 6.idf, aquitard,  layer 12 --> top=TOP_SLD6.IDF, bot=BOT_SLD6.IDF

    """

    # from here masked arrays
    nsdl = top["layer"].size
    nlayer = nsdl*2

    aquifer_layers = np.arange(1, nlayer, 2)
    aquitard_layers = np.arange(2, nlayer+1, 2)

    aquifer_top = bottom.sel(layer=slice(0, nsdl-1)).copy()
    aquifer_bottom = top.copy()
    aquifer_top["layer"] = aquifer_layers
    aquifer_bottom["layer"] = aquifer_layers

    aquitard_top = top.copy()
    aquitard_bottom = bottom.sel(layer=slice(1, nsdl)).copy()
    aquitard_top["layer"] = aquitard_layers
    aquitard_bottom["layer"] = aquitard_layers

    # calculate C for every layer
    # # Assume 1 m/d vertical k for aquifers
    # zero thickness layers are not a problem.
    aquitard_c = c
    aquitard_c["layer"]=aquitard_layers
    aquifer_c = (aquifer_top - aquifer_bottom) / K_AQUIFER
    c3d = xr.concat([aquifer_c, aquitard_c], dim="layer").sortby("layer")

    # calculate thickness for every layer
    top3d = xr.concat([aquifer_top, aquitard_top], dim="layer").sortby("layer")
    bottom3d = xr.concat([aquifer_bottom, aquitard_bottom], dim="layer").sortby("layer")
    thickness3d = top3d - bottom3d

    ##plotting layers to make sure all data looks right
    """
    x = polygon['geometry'][0].centroid.x
    yrange = polygon['geometry'][0].bounds[1::2]
    t = top3d.sel(y=slice(yrange[0], yrange[1], -1))
    b = bottom3d.sel(y=slice(yrange[0], yrange[1], -1))
    l = new_lake_bottom
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    for l in top3d['layer'].values:
        d = thickness3d.sel(layer=l).mean().values #avg thickness
        #ax.plot(top3d.sel(x=x, layer=l, method="nearest"), label=l)
        ax.fill_between(
            t.y.values,
            t.sel(x=x, layer=l, method="nearest"),
            b.sel(x=x, layer=l, method="nearest"),
            label=f'layer {l} - {d: .1}m thick',
            hatch=r"//" if l in aquitard_layers else ''
        )
    ax.plot(new_lake_bottom.y.values, new_lake_bottom.sel(x=x, method="nearest"), color='k')
    fig.legend()
    """

    # select relevant layers
    #is_relevant_layer = (bottom3d < new_lake_bottom) & (top3d >= new_lake_bottom)
    is_relevant_layer = top3d >= new_lake_bottom
    new_lake_bottom_3d = (xr.ones_like(top3d) * new_lake_bottom).where(is_relevant_layer)

    # check: lake bottom should be false for all deep layers. layer 5 and lower
    # lake_bottom_3d.sel(layer=4).sum().values==0

    # calculate new thickness for all layers
    thickness_remaining = (new_lake_bottom - bottom3d)
    thickness_remaining = thickness_remaining.where(thickness_remaining > 0)
    fraction_remaining = thickness_remaining / thickness3d
    fraction_remaining = fraction_remaining.where(fraction_remaining > 0.0, 0.0).where(is_relevant_layer)

    new_c3d = (c3d * fraction_remaining + ENTRY_RESISTANCE) # selection
    resis = new_c3d.combine_first(c3d)
    # new resistance still has the expanded layers, so collapse them to only the aquitards.
    resis_final = collapseLayers(resis, 'sum')

    new_lake_bottom_3d_collapsed = collapseLayers(new_lake_bottom_3d, 'min') # selection
    lake_bottom_final = new_lake_bottom_3d_collapsed.combine_first(lake_bottom_3d)

    #clip the outer cells to remove model artefacts of the boundary conditions
    resis_final.isel(x=slice(1,-1),y=slice(1,-1))
    lake_bottom_final.isel(x=slice(1,-1),y=slice(1,-1))

    # save new conductance and lake bottom
    #resultpath = cf.get('GeoServer','resultpath')
    Path(resultpath).mkdir(parents=True, exist_ok=True)
    # write c
    imod.idf.save(f'{resultpath}/c/*', resis_final, pattern="c{layer}.idf")
    imod.idf.save(f'{resultpath}/riv/hoofdwater/*', lake_bottom_final, pattern="both_w_l{layer}.idf")

    return resultpath
