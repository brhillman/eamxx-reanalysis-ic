"""SCRIP file for the ne<N>np4 GLL nodes, for ESMF bilinear with --dst_loc
center: centres are the nodes; corners are a tiny quad around each node
(only the centres are used for bilinear weights).

Usage: python make_ne_points_scrip.py TOPO_WITH_LATLON OUT
"""
import sys
import numpy as np, netCDF4 as nc
t = nc.Dataset(sys.argv[1])
lat, lon = t['lat_d'][:].astype(float), t['lon_d'][:].astype(float)
d = 0.01
clat = np.clip(lat[:, None] + d * np.array([-1, -1, 1, 1]), -90, 90)
clon = lon[:, None] + d * np.array([-1, 1, 1, -1])
with nc.Dataset(sys.argv[2], 'w', format='NETCDF3_64BIT_DATA') as o:
    o.createDimension('grid_size', lat.size); o.createDimension('grid_corners', 4); o.createDimension('grid_rank', 1)
    o.createVariable('grid_dims', 'i4', ('grid_rank',))[:] = lat.size
    for n, x in [('grid_center_lat', lat), ('grid_center_lon', lon), ('grid_corner_lat', clat), ('grid_corner_lon', clon)]:
        v = o.createVariable(n, 'f8', ('grid_size', 'grid_corners')[:x.ndim]); v[:] = x; v.units = 'degrees'
    o.createVariable('grid_imask', 'i4', ('grid_size',))[:] = 1
