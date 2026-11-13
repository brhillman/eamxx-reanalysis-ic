#!/bin/bash
#
# Convert ECMWF model-level GRIB (ERA5 from CDS, IFS from MARS) for make_ic.py:
#   PREFIX.3d.grib  -> PREFIX.3d.nc   (t, q, u, v, o3, clwc, ciwc, crwc, cswc)
#   PREFIX.sfc.grib -> PREFIX.sfc.nc  (lnsp, z on model level 1)
#   hybrid coefficients from the GRIB 'pv' array -> PREFIX.ab.txt
#     (two columns a [Pa] and b at the nlev+1 half levels, top -> bottom;
#      pv holds all a values followed by all b values)
#
# Usage: grib_to_nc.sh PREFIX
#   e.g. grib_to_nc.sh /pscratch/.../era5_ml/ERA5.ml.2011-05-19.18
# Needs ecCodes command-line tools (E3SM-Unified provides them).
set -e
prefix=$1
[[ -n ${prefix} ]] || { echo "usage: $0 PREFIX"; exit 1; }
for f in ${prefix}.3d.grib ${prefix}.sfc.grib; do
    [[ -f ${f} ]] || { echo "missing ${f}"; exit 1; }
done
command -v grib_to_netcdf >/dev/null || \
    source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh

# The request must have asked for a regular lat-lon grid (grid=...): the
# tool interpolates from regular lat-lon only
grid_type=$(grib_get -w count=1 -p gridType ${prefix}.3d.grib)
[[ ${grid_type} == regular_ll ]] || { echo "gridType ${grid_type}: request a regular lat-lon grid"; exit 1; }

# -D NC_FLOAT: no packing (packed shorts lose precision); -k 3: netCDF-4
for part in 3d sfc; do
    [[ -e ${prefix}.${part}.nc ]] && { echo "${prefix}.${part}.nc exists"; exit 1; }
    grib_to_netcdf -D NC_FLOAT -k 3 -o ${prefix}.${part}.nc ${prefix}.${part}.grib
done

# Hybrid coefficients (full precision; grib_get cannot print arrays)
rules=$(mktemp)
first=$(mktemp)
echo 'print "[pv%.15g!1]";' > ${rules}
grib_copy -w count=1 ${prefix}.3d.grib ${first}        # first message only
grib_filter ${rules} ${first} | awk 'NF' > ${prefix}.pv.tmp
rm -f ${rules} ${first}
nv=$(wc -l < ${prefix}.pv.tmp)
(( nv % 2 == 0 && nv > 2 )) || { echo "unexpected pv length ${nv}"; exit 1; }
nh=$(( nv / 2 ))
paste <(head -n ${nh} ${prefix}.pv.tmp) <(tail -n ${nh} ${prefix}.pv.tmp) > ${prefix}.ab.txt
rm -f ${prefix}.pv.tmp
echo "wrote ${prefix}.3d.nc ${prefix}.sfc.nc ${prefix}.ab.txt ($(( nh - 1 )) levels)"
