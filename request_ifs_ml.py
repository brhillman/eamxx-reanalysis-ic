#!/usr/bin/env python
# ==============================================================================
# Retrieve an ECMWF operational IFS analysis on model levels from MARS.
#
# Needs an ECMWF account with MARS access, the ecmwf-api-client package
# (pip install ecmwf-api-client) and ~/.ecmwfapirc
# (https://api.ecmwf.int/v1/key/). CDS does not serve operational analyses.
#
# Usage:
#   python request_ifs_ml.py --date 2011-05-19 --hour 18 --dir $SCRATCH/ifs_ml
# writes IFS.ml.<date>.<hour>.3d.grib and .sfc.grib; then run
#   grib_to_nc.sh <dir>/IFS.ml.<date>.<hour>
# The call blocks until MARS delivers (queued tape retrievals can take hours),
# so run it in the background, e.g. on the xfer QOS.
# ==============================================================================
import argparse, datetime, os
from ecmwfapi import ECMWFService


def ifs_config(date):
    """Archived model levels and an output grid matching the native
    resolution of the operational IFS on that date."""
    d = datetime.date.fromisoformat(date)
    nlev = 137 if d >= datetime.date(2013, 6, 25) else 91        # L137 from cycle 38r2
    if d >= datetime.date(2016, 3, 8):
        grid = '0.1/0.1'          # TCo1279 (~9 km), cycle 41r2 onward
    elif d >= datetime.date(2010, 1, 26):
        grid = '0.125/0.125'      # T1279 (~16 km)
    else:
        grid = '0.25/0.25'
    return nlev, grid


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--date', required=True, help='YYYY-MM-DD')
    p.add_argument('--hour', required=True, type=int)
    p.add_argument('--dir', required=True)
    a = p.parse_args()
    nlev, grid = ifs_config(a.date)
    os.makedirs(a.dir, exist_ok=True)
    common = {
        'class': 'od', 'stream': 'oper', 'type': 'an', 'expver': '1',
        'levtype': 'ml', 'date': a.date, 'time': f'{a.hour:02d}',
        # regular lat-lon output (make_ic.py interpolates from regular grids);
        # MARS interpolates from the native reduced Gaussian grid
        'grid': grid,
    }
    requests = {
        # crwc, cswc, t, u, v, q, o3, clwc, ciwc on all levels
        '3d': {**common, 'levelist': f'1/to/{nlev}', 'param': '75/76/130/131/132/133/203/246/247'},
        # lnsp and surface geopotential z on model level 1
        'sfc': {**common, 'levelist': '1', 'param': '129/152'},
    }
    server = ECMWFService('mars')
    for part, req in requests.items():
        target = os.path.join(a.dir, f'IFS.ml.{a.date}.{a.hour:02d}.{part}.grib')
        if os.path.exists(target):
            print(f'{target} exists; skipping')
            continue
        print(f'retrieving {target}: L{nlev}, grid {grid}', flush=True)
        server.execute(req, target)


if __name__ == '__main__':
    main()
