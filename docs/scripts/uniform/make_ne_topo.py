"""Write an ne<N>np4 target-grid file for make_ic.py: PHIS_d from the standard
EAMxx ne30 topography (which has no lat_d/lon_d), plus the GLL node
coordinates from an existing HICCUP ne<N>np4 IC (same TempestRemap node
order). The order is confirmed by correlating that IC's phis (remapped ERA5
surface) with PHIS_d.

Usage: python make_ne_topo.py TOPO_IN COORD_IC OUT
"""
import sys
import numpy as np, netCDF4 as nc
topo_in, coord_ic, out = sys.argv[1:4]
t, c = nc.Dataset(topo_in), nc.Dataset(coord_ic)
phis_d = t['PHIS_d'][:].astype(float)
lat, lon = c['lat'][:].astype(float), c['lon'][:].astype(float)
assert lat.size == phis_d.size, (lat.size, phis_d.size)
r = np.corrcoef(np.squeeze(c['phis'][:]), phis_d)[0, 1]
rms = np.sqrt(np.mean((np.squeeze(c['phis'][:]) - phis_d) ** 2)) / 9.80616
print(f'{lat.size} columns; corr(IC phis, PHIS_d) = {r:.4f}, rms diff {rms:.0f} m')
assert r > 0.98, 'column order mismatch'
with nc.Dataset(out, 'w', format='NETCDF4') as o:
    o.createDimension('ncol_d', lat.size)
    for n, x, u in [('lat_d', lat, 'degrees_north'), ('lon_d', lon, 'degrees_east'), ('PHIS_d', phis_d, 'm2/s2')]:
        v = o.createVariable(n, 'f8', ('ncol_d',)); v[:] = x; v.units = u
    o.source = f'PHIS_d from {topo_in}; lat_d/lon_d from {coord_ic}'
print('wrote', out)
