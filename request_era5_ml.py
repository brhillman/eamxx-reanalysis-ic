#!/usr/bin/env python
# ==============================================================================
# Request ERA5 model-level (137 hybrid levels) analysis for one date and hour
# from the Copernicus CDS (reanalysis-era5-complete, served from MARS tape).
#
# Model levels are preferred over the 37 pressure levels: ~10 levels in the
# lowest 300 m and no ECMWF below-ground extrapolated values.
#
# Needs the ecmwf-datastores-client package (installed with cdsapi) and
# ~/.cdsapirc. Tape retrievals queue for minutes to days, so submission and
# download are separate steps:
#   python request_era5_ml.py submit   --dir DIR --date 2011-05-19 --hour 18
#   python request_era5_ml.py status   --dir DIR
#   python request_era5_ml.py download --dir DIR
# Request IDs are recorded in DIR/cds_requests.json (several dates can share a
# directory). Downloads are ERA5.ml.<date>.<hour>.{3d,sfc}.grib; then run
#   grib_to_nc.sh DIR/ERA5.ml.<date>.<hour>
# ==============================================================================
import argparse, datetime, json, os, sys
from ecmwf.datastores import Client


def requests_for(date, hour, grid):
    common = {
        'class': 'ea', 'expver': '1', 'stream': 'oper', 'type': 'an',
        'levtype': 'ml', 'date': date, 'time': f'{hour:02d}:00:00',
        # MARS interpolates to a regular lat-lon grid (90 -> -90, 0 -> 360-dx)
        'grid': f'{grid}/{grid}',
    }
    stem = f'ERA5.ml.{date}.{hour:02d}'
    return {
        # 3D fields on all 137 levels: crwc, cswc, t, u, v, q, o3, clwc, ciwc
        f'{stem}.3d.grib': {**common, 'levelist': '1/to/137',
                            'param': '75/76/130/131/132/133/203/246/247'},
        # lnsp and surface geopotential z, which are archived on model level 1
        f'{stem}.sfc.grib': {**common, 'levelist': '1', 'param': '129/152'},
    }


def client():
    # Read url/key from ~/.cdsapirc (the key is never printed)
    cfg = {}
    for line in open(os.path.expanduser('~/.cdsapirc')):
        line = line.strip()
        if line and not line.startswith('#') and ':' in line:
            k, v = line.split(':', 1); cfg[k.strip()] = v.strip()
    return Client(url=cfg['url'], key=cfg['key'])


def main():
    p = argparse.ArgumentParser(description='ERA5 model-level analysis from CDS')
    p.add_argument('action', choices=['submit', 'status', 'download'])
    p.add_argument('--dir', required=True, help='download directory (holds cds_requests.json)')
    p.add_argument('--date', help='YYYY-MM-DD (submit)')
    p.add_argument('--hour', type=int, help='analysis hour, 0-23 (submit)')
    p.add_argument('--grid', default='0.25', help='output grid spacing in degrees (default 0.25, native)')
    a = p.parse_args()

    id_file = os.path.join(a.dir, 'cds_requests.json')
    ids = json.load(open(id_file)) if os.path.exists(id_file) else {}
    if a.action == 'submit':
        if a.date is None or a.hour is None:
            p.error('submit needs --date and --hour')
        datetime.date.fromisoformat(a.date)
        if not 0 <= a.hour <= 23:
            p.error('--hour must be 0-23')
    elif not ids:
        sys.exit(f'no requests recorded in {id_file}')
    os.makedirs(a.dir, exist_ok=True)
    c = client()
    if a.action == 'submit':
        for target, req in requests_for(a.date, a.hour, a.grid).items():
            if target in ids:
                print(f'{target}: already submitted ({ids[target]}), skipping')
                continue
            ids[target] = c.submit('reanalysis-era5-complete', req).request_id
            print(f'submitted {target}: {ids[target]}')
            json.dump(ids, open(id_file, 'w'), indent=2)   # record after each submit
    else:
        for target, rid in ids.items():
            r = c.get_remote(rid)
            print(f'{target}: {rid} {r.status}')
            path = os.path.join(a.dir, target)
            if a.action == 'download' and r.status == 'successful' and not os.path.exists(path):
                r.download(path); print(f'  -> {path}')


if __name__ == '__main__':
    main()
