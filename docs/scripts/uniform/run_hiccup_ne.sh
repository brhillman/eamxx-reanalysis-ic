#!/bin/bash
#SBATCH --qos=regular
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --constraint=cpu
#SBATCH --job-name=hiccup_ne
#SBATCH --output=%x.%j.out
#SBATCH --error=%x.%j.out
#
# HICCUP uniform-grid IC, timed. NE=30|120|256; NE_MAP=fv2se (HICCUP
# default, map made inside HICCUP) or bilinear (ESMF bilinear map made here
# first, timed separately). Needs TOPO_LATLON from make_ne_topo.py.
#   NE=120 NE_MAP=fv2se TOOL_DIR=$PWD sbatch --account=e3sm --export=ALL docs/scripts/uniform/run_hiccup_ne.sh
set -e
D=${TOOL_DIR}/docs/scripts/uniform
source ${D}/ne_inputs.sh
export NE TOPO WORK
export NE_MAP=${NE_MAP:-fv2se}
export HICCUP_SRC=/global/homes/b/bhillma/codes/HICCUP-latest
hiccup_env=/global/homes/b/bhillma/micromamba/envs/hiccup_env
export HDF5_USE_FILE_LOCKING=FALSE
echo "HICCUP commit: $(git -C ${HICCUP_SRC} rev-parse --short HEAD)  grid: ne${NE}np4  map: ${NE_MAP}"
if [[ ${NE_MAP} == bilinear ]]; then
    export MAP_FILE=${WORK}/maps/map_ERA5-721x1440_to_ne${NE}np4_esmfbilin.20261113.nc
    (
    source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh
    python ${D}/make_ne_points_scrip.py ${TOPO_LATLON} ${WORK}/grids/ne${NE}np4_points_scrip.nc
    echo "=== ESMF bilinear map"
    srun -n 1 /usr/bin/time -v ESMF_RegridWeightGen -s /pscratch/sd/b/bhillma/conus200/hiccup_x4/grids/scrip_ERA5_721x1440.cdf5.nc \
        -d ${WORK}/grids/ne${NE}np4_points_scrip.nc -w ${MAP_FILE} -m bilinear --dst_loc center \
        --ignore_unmapped --ignore_degenerate 2>&1 | grep -v "^ *$" | tail -25
    )
fi
export PATH=${hiccup_env}/bin:${PATH}
export PYTHONPATH=${HICCUP_SRC}
echo "=== HICCUP"
/usr/bin/time -v python -u ${D}/hiccup_ne.py
