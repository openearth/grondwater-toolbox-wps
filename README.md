<h1> Groundwater toolbox procesess </h1>
  <p>Description of tools of groundwater toolbox. An online user friendly interface that enables quickscans of effects on groundwater via application of [LHM](https:\\nhi.nu).</p>p
</hr>

# grondwater-toolbox-wps
PyWPS processes for Grondwater Toolbox. These processes enable online interaction with groundwatermodel of the Netherlands (LHM, Dutch Hydrological Model). More information about LHM can be found at [nhi.nu] (https:\\nhi.nu). 

# process description
Currently (July 2025) the grondwater toolbox consists of 4 possible processes

# installation instructions
Install using the brl_env_2024_hist.yml with your prefered conda package manager. This is a bit cumbersome due to the various dependencies in the iMOD package

# usage (local)
For basic deployment of a PyWPS on flask you should:
<ul>
  <li>Add your wps processes in the processes folder</li>
  <li>Edit `requirements.txt` with the required packages</li>
  <li>Edit `pywps.wsgi` to import the processes you want to deploy</li>
  <li>Edit `pywps.cfg` with your details</li>
  </li>
</ul>

Start the local server of PyWPS by starting up the prefered conda package manager (miniforge is an example) prompt with the following
<ul>
  <li>activate the PyWPS environment (activate grondwater-toolbox-wps)</li>
  <li>navigate to the directory where the pywps.wsgi resides</li>
  <li>type python pywps.wsgi</li>
</ul>
If everything is well, you should see the 
  


