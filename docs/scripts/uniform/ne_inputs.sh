# Per-grid inputs for the uniform-grid comparison (sourced; needs NE).
# TOPO: the EAMxx default topography (namelist_defaults_eamxx.xml).
# COORD_IC: an existing HICCUP IC on the grid, for GLL node coordinates.
I=/global/cfs/cdirs/e3sm/inputdata
case ${NE} in
    30)  TOPO=${I}/atm/cam/topo/USGS-gtopo30_ne30np4pg2_x6t-SGH.c20210614.nc ;;
    120) TOPO=${I}/atm/cam/topo/USGS-gtopo30_ne120np4pg2_x6t_20230404.nc ;;
    256) TOPO=${I}/atm/cam/topo/USGS-gtopo30_ne256np4pg2_x6t-SGH.c20210614.nc ;;
    1024) TOPO=${I}/atm/cam/topo/USGS-gtopo30_ne1024np4pg2_x6t-SGH.c20210614.nc ;;
    *) echo "unsupported NE=${NE}"; exit 1 ;;
esac
COORD_IC=${I}/atm/scream/init/eamxxi_ne${NE}np4L128v4_ERA5-20190101_c20260922.nc
# ne1024: the HICCUP IC used by the conus200 ne1024 runs (runscripts/conus200_inputs.sh)
[[ ${NE} == 1024 ]] && COORD_IC=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_init/HICCUP.atm_era5.2011-05-19.18.ne1024np4.L128v4.20260918.nc
WORK=/pscratch/sd/b/bhillma/conus200/ne30_ic
TOPO_LATLON=${WORK}/grids/topo_ne${NE}np4_latlon.nc
