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
# Make an EAMxx IC with make_ic.py: init (if not yet initialized), fill
# columns with one task per node (numba threads within the node), then check
# sampled columns. Rerunning resumes: finished chunks are skipped.
#
# All inputs are set explicitly below; override any of them through the
# environment, e.g.
#   GRID=1024x2 SOURCE=era5-ml sbatch run_make_ic.sh
#   GRID=128x2 SOURCE=merra2-pl sbatch --nodes=1 --qos=debug --time=00:30:00 run_make_ic.sh
# SOURCE: era5-ml, ifs-ml, merra2-ml (model levels, preferred), era5-pl, merra2-pl
set -e

grid=${GRID:-1024x2}
source_type=${SOURCE:-era5-ml}
date=${DATE:-2011-05-19}
hour=${HOUR:-18}
horiz=${HORIZ:-bicubic}
work=${WORK:-/pscratch/sd/b/bhillma/conus200/era5_ic}
tag=${TAG:-$(date +%Y%m%d)}
ymd=${date//-/}

topo=${TOPO:-/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_topo/USGS-topo_2026-incite-conus-${grid}-np4_smoothedx6t_20251121.nc}
vert=${VERT:-/global/homes/b/bhillma/codes/HICCUP-latest/files_vert/L128_for_E3SMv4_c20260820.nc}

# Default source files (CONUS 2026 INCITE work on Perlmutter)
era5_pl_dir=/pscratch/sd/b/bhillma/conus200/hiccup_x4/era5
era5_ml_dir=/pscratch/sd/b/bhillma/conus200/hiccup_x4/era5_ml
ifs_ml_dir=/pscratch/sd/b/bhillma/conus200/ifs_ml
merra2_np_dir=/global/cfs/projectdirs/m3522/cmip6/MERRA2/inst3_3d_asm_Np/${date:0:4}
merra2_nv_dir=/pscratch/sd/b/bhillma/conus200/merra2_nv
case ${source_type} in
    era5-ml)   atm=${era5_ml_dir}/ERA5.ml.${date}.${hour}.3d.nc
               sfc=${era5_ml_dir}/ERA5.ml.${date}.${hour}.sfc.nc
               ab=${era5_ml_dir}/ERA5.ml.${date}.${hour}.ab.txt
               ref=${era5_pl_dir}/ERA5.atm.${date}.${hour}.nc ;;
    ifs-ml)    atm=${ifs_ml_dir}/IFS.ml.${date}.${hour}.3d.nc
               sfc=${ifs_ml_dir}/IFS.ml.${date}.${hour}.sfc.nc
               ab=${ifs_ml_dir}/IFS.ml.${date}.${hour}.ab.txt
               ref=${era5_pl_dir}/ERA5.atm.${date}.${hour}.nc ;;   # no IFS z500 here: ERA5 as reference
    era5-pl)   atm=${era5_pl_dir}/ERA5.atm.${date}.${hour}.nc
               sfc=${era5_pl_dir}/ERA5.sfc.${date}.${hour}.nc
               ab=""
               ref=${atm} ;;
    merra2-ml) atm=$(ls ${merra2_nv_dir}/MERRA2_*.inst3_3d_asm_Nv.${ymd}.nc4 2>/dev/null | head -1)
               sfc=""; ab=""
               ref=$(ls ${merra2_np_dir}/MERRA2_*.inst3_3d_asm_Np.${ymd}.nc4 | head -1) ;;
    merra2-pl) atm=$(ls ${merra2_np_dir}/MERRA2_*.inst3_3d_asm_Np.${ymd}.nc4 | head -1)
               sfc=""; ab=""
               ref=${atm} ;;
    *) echo "unknown SOURCE ${source_type}"; exit 1 ;;
esac
atm=${ATM:-${atm}}; sfc=${SFC:-${sfc}}; ab=${AB:-${ab}}; ref=${REF:-${ref}}
opts=""
[[ -n ${sfc} ]] && opts+=" --sfc ${sfc}"
[[ -n ${ab}  ]] && opts+=" --ab ${ab}"
out=${OUT:-${work}/eamxx_ic.${source_type}.${date}.${hour}.${grid}.L128v4.${horiz}.${tag}.nc}

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
        --atm ${atm} ${opts} \
        --topo ${topo} --vert ${vert} --date ${date} --hour ${hour} --horiz ${horiz}
fi

time srun --cpu-bind=none python ${tool}/make_ic.py run --out ${out}

python ${tool}/make_ic.py check --out ${out} --ref-pl ${ref}
