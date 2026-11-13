"""ERA5 verification fields for the IC test runs: 6-hourly analyses from
2011-05-19 18Z to 2011-05-22 18Z (pressure levels 200/500/850 hPa: z, t, u,
v, q; single levels: msl, tcwv, tclw, tciw) and hourly total precipitation.

Usage: python request_era5_verif.py OUTDIR   (uses ~/.cdsapirc; blocks until done)
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from request_era5_ml import client
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
days = ['19', '20', '21', '22']
six = ['00:00', '06:00', '12:00', '18:00']
base = {'product_type': ['reanalysis'], 'year': ['2011'], 'month': ['05'], 'day': days,
        'data_format': 'netcdf', 'download_format': 'unarchived'}
reqs = {
    'ERA5.verif.pl.nc': ('reanalysis-era5-pressure-levels',
        {**base, 'time': six, 'pressure_level': ['200', '500', '850'],
         'variable': ['geopotential', 'temperature', 'u_component_of_wind', 'v_component_of_wind', 'specific_humidity']}),
    'ERA5.verif.sfc.nc': ('reanalysis-era5-single-levels',
        {**base, 'time': six, 'variable': ['mean_sea_level_pressure', 'total_column_water_vapour',
                                           'total_column_cloud_liquid_water', 'total_column_cloud_ice_water']}),
    'ERA5.verif.tp.nc': ('reanalysis-era5-single-levels',
        {**base, 'time': [f'{h:02d}:00' for h in range(24)], 'variable': ['total_precipitation']}),
}
c = client()
for f, (ds, r) in reqs.items():
    t = os.path.join(out, f)
    if os.path.exists(t): print('exists', t); continue
    c.retrieve(ds, r, t); print('wrote', t)
