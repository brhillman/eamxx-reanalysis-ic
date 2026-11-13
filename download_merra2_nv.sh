#!/bin/bash
#
# Download one day of MERRA-2 inst3_3d_asm_Nv (72 model levels, 3-hourly)
# from NASA GES DISC.
#
# Needs a NASA Earthdata login (https://urs.earthdata.nasa.gov) with the
# "NASA GESDISC DATA ARCHIVE" application approved, and in ~/.netrc:
#   machine urs.earthdata.nasa.gov login <user> password <password>
# (chmod 600 ~/.netrc).
#
# Usage: download_merra2_nv.sh YYYY-MM-DD OUTDIR
set -e
date=$1; outdir=$2
[[ -n ${date} && -n ${outdir} ]] || { echo "usage: $0 YYYY-MM-DD OUTDIR"; exit 1; }
y=${date:0:4}; m=${date:5:2}; ymd=${date//-/}
grep -q urs.earthdata.nasa.gov ~/.netrc 2>/dev/null || { echo "no Earthdata entry in ~/.netrc"; exit 1; }

# MERRA-2 stream number by year (4x1 marks a reprocessed month, so try both)
if   (( y <= 1991 )); then streams="100"
elif (( y <= 2000 )); then streams="200"
elif (( y <= 2010 )); then streams="300"
else                       streams="400 401"
fi

mkdir -p ${outdir}
cookies=$(mktemp)
for s in ${streams}; do
    f=MERRA2_${s}.inst3_3d_asm_Nv.${ymd}.nc4
    url=https://goldsmr5.gesdisc.eosdis.nasa.gov/data/MERRA2/M2I3NVASM.5.12.4/${y}/${m}/${f}
    if curl -fsS -n -c ${cookies} -b ${cookies} -L -o ${outdir}/${f}.part ${url}; then
        mv ${outdir}/${f}.part ${outdir}/${f}
        rm -f ${cookies}
        echo "downloaded ${outdir}/${f}"
        exit 0
    fi
    rm -f ${outdir}/${f}.part
done
rm -f ${cookies}
echo "download failed for ${date} (streams ${streams})"
exit 1
