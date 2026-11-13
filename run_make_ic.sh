#!/bin/bash
#SBATCH --qos=regular
#SBATCH --time=01:00:00
#SBATCH --nodes=8
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=256
#SBATCH --constraint=cpu
#SBATCH --job-name=eamxx_ic
#SBATCH --output=%x.%j.out
#SBATCH --error=%x.%j.out
#
# Make an EAMxx IC with make_ic.py: init (if not yet initialized), fill
# columns with one task per node (numba threads within the node), then check
# sampled columns. Rerunning resumes: finished chunks are skipped.
# The #SBATCH lines are for Perlmutter CPU nodes; pass --account (and any
# other changes) on the sbatch command line.
#
# Inputs come from the environment. Required:
#   SOURCE    era5-ml, ifs-ml, merra2-ml (model levels, preferred), era5-pl, merra2-pl
#   DATE      YYYY-MM-DD
#   HOUR      analysis hour (0-23)
#   TOPO      EAMxx topography file with lat_d, lon_d, PHIS_d (sets the target grid)
#   VERT      vertical grid file with hyam, hybm, hyai, hybi (P0)
#   WORK      output directory
#   SRC_DIR   directory with the source files, named as the download scripts
#             write them (below); or give ATM/SFC/AB explicitly
# Optional:
#   ATM, SFC, AB   source files, overriding the names derived from SRC_DIR
#   REF       pressure-level file with z (ERA5) or H (MERRA-2) at 500 hPa for
#             the hydrostatic check; default: found in SRC_DIR if present
#   GRID      grid label for the output name (default: TOPO basename)
#   HORIZ     bicubic (default) or bilinear
#   TAG       output name suffix (default: today, YYYYMMDD)
#   OUT       full output path (overrides WORK/GRID/TAG naming)
#   ENV_SETUP script to source for python with numba and netCDF4
#             (default: E3SM-Unified on Perlmutter; set empty to skip)
#   TOOL_DIR  directory with make_ic.py (default: this script's directory or
#             the submit directory)
#
# Example:
#   SOURCE=era5-ml DATE=2011-05-19 HOUR=18 TOPO=topo.nc VERT=L128.nc \
#     WORK=$SCRATCH/ic SRC_DIR=$SCRATCH/era5_ml sbatch --account=XXX run_make_ic.sh
set -e

need() { [[ -n ${!1} ]] || { echo "error: $1 is not set (see the header of run_make_ic.sh)"; exit 1; }; }
for v in SOURCE DATE HOUR TOPO VERT WORK; do need $v; done
[[ -n ${SRC_DIR} || -n ${ATM} ]] || { echo "error: set SRC_DIR or ATM"; exit 1; }

source_type=${SOURCE}
date=${DATE}
hour=$(printf %02d $((10#${HOUR})))
horiz=${HORIZ:-bicubic}
topo=${TOPO}
vert=${VERT}
work=${WORK}
src=${SRC_DIR}
grid=${GRID:-$(basename ${topo} .nc)}
tag=${TAG:-$(date +%Y%m%d)}
ymd=${date//-/}

# Source file names as written by request_era5_ml.py / request_ifs_ml.py +
# grib_to_nc.sh, download_merra2_nv.sh, and the GES DISC MERRA-2 Np archive.
# ERA5 pressure levels: ERA5.atm.<date>.<hour>.nc and ERA5.sfc.<date>.<hour>.nc.
first() { ls $1 2>/dev/null | head -1; }
case ${source_type} in
    era5-ml)   atm=${src}/ERA5.ml.${date}.${hour}.3d.nc
               sfc=${src}/ERA5.ml.${date}.${hour}.sfc.nc
               ab=${src}/ERA5.ml.${date}.${hour}.ab.txt
               ref=$(first "${src}/ERA5.atm.${date}.${hour}.nc") ;;
    ifs-ml)    atm=${src}/IFS.ml.${date}.${hour}.3d.nc
               sfc=${src}/IFS.ml.${date}.${hour}.sfc.nc
               ab=${src}/IFS.ml.${date}.${hour}.ab.txt
               ref=$(first "${src}/ERA5.atm.${date}.${hour}.nc") ;;   # no IFS z500 file: ERA5 if present
    era5-pl)   atm=${src}/ERA5.atm.${date}.${hour}.nc
               sfc=${src}/ERA5.sfc.${date}.${hour}.nc
               ab=""
               ref=${atm} ;;
    merra2-ml) atm=$(first "${src}/MERRA2_*.inst3_3d_asm_Nv.${ymd}.nc4")
               sfc=""; ab=""
               ref=$(first "${src}/MERRA2_*.inst3_3d_asm_Np.${ymd}.nc4") ;;
    merra2-pl) atm=$(first "${src}/MERRA2_*.inst3_3d_asm_Np.${ymd}.nc4")
               sfc=""; ab=""
               ref=${atm} ;;
    *) echo "error: unknown SOURCE ${source_type}"; exit 1 ;;
esac
atm=${ATM:-${atm}}; sfc=${SFC:-${sfc}}; ab=${AB:-${ab}}; ref=${REF:-${ref}}
for f in "${atm}" "${sfc}" "${ab}" "${ref}" "${topo}" "${vert}"; do
    [[ -z ${f} || -f ${f} ]] || { echo "error: missing input ${f}"; exit 1; }
done
[[ -n ${atm} ]] || { echo "error: no ${source_type} file for ${date} in ${src}"; exit 1; }
opts=""
[[ -n ${sfc} ]] && opts+=" --sfc ${sfc}"
[[ -n ${ab}  ]] && opts+=" --ab ${ab}"
out=${OUT:-${work}/eamxx_ic.${source_type}.${date}.${hour}.${grid}.$(basename ${vert} .nc).${horiz}.${tag}.nc}

env_setup=${ENV_SETUP-/global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh}
[[ -n ${env_setup} ]] && source ${env_setup}
export NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-128}
export HDF5_USE_FILE_LOCKING=FALSE
tool=${TOOL_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}
[[ -f ${tool}/make_ic.py ]] || tool=${SLURM_SUBMIT_DIR}
[[ -f ${tool}/make_ic.py ]] || { echo "error: make_ic.py not found; set TOOL_DIR"; exit 1; }
echo "tool: ${tool}  python: $(which python)"
echo "out:  ${out}"

mkdir -p $(dirname ${out})
# Stripe new files across Lustre OSTs for parallel writes (no-op elsewhere)
lfs setstripe -c 32 -S 16M $(dirname ${out}) 2>/dev/null || true
if [[ ! -e ${out}.status/config.json ]]; then
    python ${tool}/make_ic.py init --out ${out} --source ${source_type} \
        --atm ${atm} ${opts} \
        --topo ${topo} --vert ${vert} --date ${date} --hour ${hour} --horiz ${horiz}
fi

time srun --cpu-bind=none python ${tool}/make_ic.py run --out ${out}

python ${tool}/make_ic.py check --out ${out} ${ref:+--ref-pl ${ref}}
