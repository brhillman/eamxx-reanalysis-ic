#!/bin/bash
#SBATCH --qos=regular
#SBATCH --time=01:00:00
#SBATCH --nodes=8
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=256
#SBATCH --constraint=cpu
#SBATCH --account=e3sm
#SBATCH --job-name=era5_ic
#SBATCH --output=%x.%j.out
#SBATCH --error=%x.%j.out
#
# Make an EAMxx IC from ERA5 with make_ic.py: init (if not yet initialized),
# fill columns with one task per node (numba threads within the node), then
# check sampled columns. Rerunning resumes: finished chunks are skipped.
#
# All inputs are set explicitly below; override any of them through the
# environment, e.g.
#   GRID=1024x2 sbatch run_make_ic.sh
#   GRID=128x2 SOURCE=pl sbatch --nodes=1 --qos=debug --time=00:30:00 run_make_ic.sh
set -e

grid=${GRID:-1024x2}
source_type=${SOURCE:-ml}                   # ml (ERA5 model levels) or pl
date=${DATE:-2011-05-19}
hour=${HOUR:-18}
horiz=${HORIZ:-bicubic}
work=${WORK:-/pscratch/sd/b/bhillma/conus200/era5_ic}
tag=${TAG:-$(date +%Y%m%d)}

topo=${TOPO:-/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_topo/USGS-topo_2026-incite-conus-${grid}-np4_smoothedx6t_20251121.nc}
vert=${VERT:-/global/homes/b/bhillma/codes/HICCUP-latest/files_vert/L128_for_E3SMv4_c20260820.nc}
era5_pl_atm=/pscratch/sd/b/bhillma/conus200/hiccup_x4/era5/ERA5.atm.${date}.${hour}.nc
era5_pl_sfc=/pscratch/sd/b/bhillma/conus200/hiccup_x4/era5/ERA5.sfc.${date}.${hour}.nc
era5_ml_dir=/pscratch/sd/b/bhillma/conus200/hiccup_x4/era5_ml
if [[ ${source_type} == ml ]]; then
    era5_atm=${ERA5_ATM:-${era5_ml_dir}/ERA5.ml.${date}.${hour}.3d.nc}
    era5_sfc=${ERA5_SFC:-${era5_ml_dir}/ERA5.ml.${date}.${hour}.sfc.nc}
    era5_ab=${ERA5_AB:-${era5_ml_dir}/ERA5.ml.L137_ab.txt}
    ab_opt="--era5-ab ${era5_ab}"
else
    era5_atm=${ERA5_ATM:-${era5_pl_atm}}
    era5_sfc=${ERA5_SFC:-${era5_pl_sfc}}
    ab_opt=""
fi
out=${OUT:-${work}/eamxx_ic.era5${source_type}.${date}.${hour}.${grid}.L128v4.${horiz}.${tag}.nc}

# Python with numba/netCDF4 from E3SM-Unified
source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh
export NUMBA_NUM_THREADS=128
export HDF5_USE_FILE_LOCKING=FALSE
tool=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
[[ -f ${tool}/make_ic.py ]] || tool=${SLURM_SUBMIT_DIR}
echo "tool: ${tool}  python: $(which python)"
echo "out:  ${out}"

mkdir -p ${work}
# Stripe new files in the work directory across OSTs for parallel writes
lfs setstripe -c 32 -S 16M ${work} 2>/dev/null || true
if [[ ! -e ${out}.status/config.json ]]; then
    python ${tool}/make_ic.py init --out ${out} --source ${source_type} \
        --era5-atm ${era5_atm} --era5-sfc ${era5_sfc} ${ab_opt} \
        --topo ${topo} --vert ${vert} --date ${date} --hour ${hour} --horiz ${horiz}
fi

time srun --cpu-bind=none python ${tool}/make_ic.py run --out ${out}

python ${tool}/make_ic.py check --out ${out} --era5-pl-atm ${era5_pl_atm}
