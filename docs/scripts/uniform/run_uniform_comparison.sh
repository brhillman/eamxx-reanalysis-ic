#!/bin/bash
#SBATCH --nodes=1
#SBATCH --constraint=cpu
#SBATCH --qos=debug
#SBATCH --time=00:30:00
#
# Comparison diagnostics on a uniform grid (2011-05-19 18Z):
#   NE=120 TOOL_DIR=$PWD sbatch --account=e3sm --export=ALL docs/scripts/uniform/run_uniform_comparison.sh
# (ne30 is small enough to run directly with bash.)
set -e
D=${TOOL_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}/docs/scripts
source ${D}/uniform/ne_inputs.sh
P=/global/common/software/e3sm/anaconda_envs/e3smu_1_13_0/pm-cpu/pixi/.pixi/envs/default/bin/python
S=/pscratch/sd/b/bhillma/conus200
ML=${S}/hiccup_x4/era5_ml
PL=${S}/hiccup_x4/era5/ERA5.atm.2011-05-19.18.nc
O=${WORK}/output
g=ne${NE}np4
files=("HICCUP default (fv2se_flx)=${O}/HICCUP.atm_era5.2011-05-19.18.${g}.L128v4.fv2se.20261113.nc"
       "HICCUP bilinear=${O}/HICCUP.atm_era5.2011-05-19.18.${g}.L128v4.bilinear.20261113.nc"
       "new tool, ERA5 pressure levels=${O}/eamxx_ic.era5-pl.2011-05-19.18.${g}.L128_for_E3SMv4_c20260820.bicubic.20261113.nc"
       "new tool=${O}/eamxx_ic.era5-ml.2011-05-19.18.${g}.L128_for_E3SMv4_c20260820.bicubic.20261113.nc")
OUT=${WORK}/comparison; mkdir -p ${OUT}
${P} ${D}/ic_diagnostics.py ${TOPO_LATLON} ${ML} ${PL} "${files[@]}" | tee ${OUT}/diagnostics.${g}.md
# wind vs surface-height mismatch, all columns and Wyoming box
BOX=-90,90,0,360 NAME=global PL=${PL} ${P} ${D}/terrain_metrics.py ${TOPO_LATLON} ${ML} ${OUT}/wind_global.${g}.png "${files[@]}" | tee ${OUT}/terrain_global.${g}.md
