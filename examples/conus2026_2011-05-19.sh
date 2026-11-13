#!/bin/bash
#
# Example: the CONUS 2026 INCITE RRM initial conditions (2011-05-19 18Z,
# L128 E3SMv4 levels) on Perlmutter. Sets the inputs and submits
# run_make_ic.sh; extra arguments go to sbatch.
#
#   GRID=1024x2 SOURCE=era5-ml examples/conus2026_2011-05-19.sh
#   GRID=128x2  SOURCE=merra2-pl examples/conus2026_2011-05-19.sh --nodes=1 --qos=debug --time=00:30:00
set -e
export GRID=${GRID:-1024x2}
export SOURCE=${SOURCE:-era5-ml}
export DATE=2011-05-19 HOUR=18
export TOPO=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_topo/USGS-topo_2026-incite-conus-${GRID}-np4_smoothedx6t_20251121.nc
export VERT=${VERT:-/global/homes/b/bhillma/codes/HICCUP-latest/files_vert/L128_for_E3SMv4_c20260820.nc}
export WORK=${WORK:-/pscratch/sd/b/bhillma/conus200/era5_ic}
era5_pl=/pscratch/sd/b/bhillma/conus200/hiccup_x4/era5
case ${SOURCE} in
    era5-ml)   export SRC_DIR=/pscratch/sd/b/bhillma/conus200/hiccup_x4/era5_ml ;;
    ifs-ml)    export SRC_DIR=/pscratch/sd/b/bhillma/conus200/ifs_ml ;;
    era5-pl)   export SRC_DIR=${era5_pl} ;;
    merra2-ml) export SRC_DIR=/pscratch/sd/b/bhillma/conus200/merra2_nv ;;
    merra2-pl) export SRC_DIR=/global/cfs/projectdirs/m3522/cmip6/MERRA2/inst3_3d_asm_Np/${DATE:0:4} ;;
esac
# Hydrostatic check reference: ERA5 pressure levels for ECMWF sources, MERRA-2 Np for MERRA-2
case ${SOURCE} in
    era5-ml|ifs-ml) export REF=${era5_pl}/ERA5.atm.${DATE}.${HOUR}.nc ;;
    merra2-ml)      export REF=$(ls /global/cfs/projectdirs/m3522/cmip6/MERRA2/inst3_3d_asm_Np/${DATE:0:4}/MERRA2_*.inst3_3d_asm_Np.${DATE//-/}.nc4 | head -1) ;;
esac
export TOOL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mkdir -p ${WORK}/logs
sbatch --account=e3sm --job-name=eamxx_ic_${GRID}_${SOURCE} --output=${WORK}/logs/%x.%j.out --error=${WORK}/logs/%x.%j.out "$@" ${TOOL_DIR}/run_make_ic.sh
