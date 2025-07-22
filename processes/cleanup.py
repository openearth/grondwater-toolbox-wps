#script to clean up GeoServer workspaces and tmp files of PyWPS processes

from brl_utils import read_config, cleanup_pywps_tmp
from brl_utils_geoserver import cleanup_workspace_geoserver
import sys

if __name__ == "__main__":
    cf = read_config()
    if cf is None:
        print("Configuration file not found or could not be read.")
        sys.exit(1)
    try:
        rest_url = cf.get("GeoServer", "rest_url")
        user = cf.get("GeoServer", "user")
        pw = cf.get("GeoServer", "pass")

        workspaces = [ws.strip() for ws in cf.get("GeoServer", "workspaces_to_clean").split(",") if ws.strip()]

        for ws in workspaces:
            print(f"\n▶ Cleaning up workspace: {ws}")
            cleanup_workspace_geoserver(rest_url, user, pw, ws)
    except Exception as e:
        print(f"Error during GeoServer cleanup: {e}")
           
    
    try:
        tmp_dir = cf.get("wps", "tmp")
        cleanup_pywps_tmp(tmp_dir)
    except Exception as e:
        print(f"Error during PyWPS temporary files cleanup: {e}")
