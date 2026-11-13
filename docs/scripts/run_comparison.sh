#!/bin/bash
#SBATCH --nodes=1
#SBATCH --constraint=cpu
#SBATCH --qos=debug
#SBATCH --time=00:30:00
#
# Run the HICCUP comparison diagnostics for one CONUS grid (2011-05-19 18Z).
#   GRID=1024x2 sbatch --account=e3sm docs/scripts/run_comparison.sh
# Paths are the Perlmutter locations used in docs/comparison_with_hiccup.md.
set -e
GRID=${GRID:-1024x2}
D=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
[[ -f ${D}/ic_diagnostics.py ]] || D=${TOOL_DIR}/docs/scripts     # sbatch copies the script
P=/global/common/software/e3sm/anaconda_envs/e3smu_1_13_0/pm-cpu/pixi/.pixi/envs/default/bin/python
C=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM
S=/pscratch/sd/b/bhillma/conus200
TOPO=${C}/files_topo/USGS-topo_2026-incite-conus-${GRID}-np4_smoothedx6t_20251121.nc
ML=${S}/hiccup_x4/era5_ml
PL=${S}/hiccup_x4/era5/ERA5.atm.2011-05-19.18.nc
NEW=${S}/era5_ic/eamxx_ic.era5-ml.2011-05-19.18.${GRID}.L128_for_E3SMv4_c20260820.bicubic
files=("HICCUP conservative (20260918, in use)=${C}/files_init/HICCUP.atm_era5.2011-05-19.18.${GRID}.L128v4.20260918.nc"
       "HICCUP bilinear (20261113)=${S}/hiccup_x4/output/HICCUP.atm_era5.2011-05-19.18.${GRID}.L128v4.20261113.nc")
[[ -f ${NEW}.pmwind.20261112.nc ]] && files+=("new tool, pressure-matched winds=${NEW}.pmwind.20261112.nc")
files+=("new tool (20261113)=${NEW}.20261113.nc")
OUT=${OUT:-${S}/era5_ic/comparison}
mkdir -p ${OUT}
${P} ${D}/ic_diagnostics.py ${TOPO} ${ML} ${PL} "${files[@]}" | tee ${OUT}/diagnostics.${GRID}.md
${P} ${D}/terrain_metrics.py ${TOPO} ${ML} ${OUT}/wyoming_wind.${GRID}.png "${files[@]}" | tee ${OUT}/terrain.${GRID}.md
${P} ${D}/imprint_maps.py ${TOPO} ${OUT}/wyoming_imprint.${GRID}.png "${files[0]}" "${files[1]}" "${files[-1]}"
