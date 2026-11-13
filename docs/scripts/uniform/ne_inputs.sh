# Per-grid inputs for the uniform-grid comparison (sourced; needs NE).
# TOPO: the EAMxx default topography (namelist_defaults_eamxx.xml).
# COORD_IC: an existing HICCUP IC on the grid, for GLL node coordinates.
I=/global/cfs/cdirs/e3sm/inputdata
case ${NE} in
    30)  TOPO=${I}/atm/cam/topo/USGS-gtopo30_ne30np4pg2_x6t-SGH.c20210614.nc ;;
    120) TOPO=${I}/atm/cam/topo/USGS-gtopo30_ne120np4pg2_x6t_20230404.nc ;;
    256) TOPO=${I}/atm/cam/topo/USGS-gtopo30_ne256np4pg2_x6t-SGH.c20210614.nc ;;
    *) echo "unsupported NE=${NE}"; exit 1 ;;
esac
COORD_IC=${I}/atm/scream/init/eamxxi_ne${NE}np4L128v4_ERA5-20190101_c20260922.nc
WORK=/pscratch/sd/b/bhillma/conus200/ne30_ic
TOPO_LATLON=${WORK}/grids/topo_ne${NE}np4_latlon.nc
