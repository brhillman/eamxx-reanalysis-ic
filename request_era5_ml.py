#!/usr/bin/env python
# ==============================================================================
# Request ERA5 model-level (137 hybrid levels) analysis for the CONUS IC date
# from the Copernicus CDS (reanalysis-era5-complete, served from MARS tape).
#
# Model levels replace the 37 pressure levels HICCUP used: ~10 levels in the
# lowest 300 m and no ECMWF below-ground extrapolated values.
#
# Usage (needs cdsapi and ~/.cdsapirc; on Perlmutter cdsapi is installed with
#   pip install --target ~/.local/cdsapi-pkgs cdsapi, so set
#   PYTHONPATH=~/.local/cdsapi-pkgs and use the hiccup_env python):
#   python request_era5_ml.py submit     # submit, record request IDs, return
#   python request_era5_ml.py status     # show the state of recorded requests
#   python request_era5_ml.py download   # download completed requests
# ==============================================================================
import json, os, sys
from ecmwf.datastores import Client

work_dir  = '/pscratch/sd/b/bhillma/conus200/hiccup_x4/era5_ml'
id_file   = f'{work_dir}/cds_requests.json'
date, hour = '2011-05-19', '18'

common = {
    'class': 'ea', 'expver': '1', 'stream': 'oper', 'type': 'an',
    'levtype': 'ml', 'date': date, 'time': f'{hour}:00:00',
    # MARS interpolates to the same 0.25 deg grid as the pressure-level data
    # (90 -> -90, 0 -> 359.75)
    'grid': '0.25/0.25',
}
requests = {
    # 3D fields on all 137 levels: crwc, cswc, t, u, v, q, o3, clwc, ciwc
    f'ERA5.ml.{date}.{hour}.3d.grib': {**common, 'levelist': '1/to/137',
        'param': '75/76/130/131/132/133/203/246/247'},
    # lnsp and surface geopotential z, which are archived on model level 1
    f'ERA5.ml.{date}.{hour}.sfc.grib': {**common, 'levelist': '1',
        'param': '129/152'},
}

def client():
    # Read url/key from ~/.cdsapirc (key is never printed)
    cfg = {}
    for line in open(os.path.expanduser('~/.cdsapirc')):
        line = line.strip()
        if line and not line.startswith('#') and ':' in line:
            k, v = line.split(':', 1); cfg[k.strip()] = v.strip()
    return Client(url=cfg['url'], key=cfg['key'])

def main(action):
    os.makedirs(work_dir, exist_ok=True)
    c = client()
    if action == 'submit':
        if os.path.exists(id_file): sys.exit(f'{id_file} exists; requests already submitted')
        ids = {}
        for target, req in requests.items():
            r = c.submit('reanalysis-era5-complete', req)
            ids[target] = r.request_id
            print(f'submitted {target}: {r.request_id}')
        json.dump(ids, open(id_file, 'w'), indent=2)
    else:
        ids = json.load(open(id_file))
        for target, rid in ids.items():
            r = c.get_remote(rid)
            print(f'{target}: {rid} {r.status}')
            if action == 'download' and r.status == 'successful':
                path = f'{work_dir}/{target}'
                if not os.path.exists(path): r.download(path); print(f'  -> {path}')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'status')
