"""HICCUP (latest checkout) EAMxx IC on a uniform neXXnp4 grid, L128v4,
ERA5 2011-05-19 18Z. Follows template_hiccup_scripts/
create_EAMxx_IC_from_ERA5-NOAA.py (atmosphere only).

Environment: NE (30, 120, 256), WORK, HICCUP_SRC, TOPO (EAMxx default
topography for the grid), and NE_MAP:
  fv2se     HICCUP's default: makes the ERA5 and ne grids and an ncremap
            fv2se_flx (conservative, TempestRemap) map itself
  bilinear  a pre-made ESMF bilinear map (MAP_FILE), as used for the
            regenerated CONUS HICCUP ICs
"""
import os
from hiccup import hiccup
work, ne, kind = os.environ['WORK'], os.environ['NE'], os.getenv('NE_MAP', 'fv2se')
hiccup_root = os.environ['HICCUP_SRC']
date, hour = '2011-05-19', '18'
era5 = '/pscratch/sd/b/bhillma/conus200/hiccup_x4/era5'
grid = f'ne{ne}np4'
out = f'{work}/output/HICCUP.atm_era5.{date}.{hour}.{grid}.L128v4.{kind}.20261113.nc'
# Relative paths: with absolute paths under this work directory, TempestRemap's
# GenerateOverlapMesh (called by ncremap) aborts with "buffer overflow
# detected" at ne120 (long --out path); ne30 happened to fit.
os.chdir(work)
tmp = f'tmp_{grid}_{kind}'
os.makedirs(tmp, exist_ok=True)

h = hiccup.create_hiccup_data(src_data_name='ERA5', target_model='EAMXX',
                              dst_horz_grid=grid, dst_vert_grid='L128v4',
                              input_file_list=[f'{era5}/ERA5.atm.{date}.{hour}.nc',
                                               f'{era5}/ERA5.sfc.{date}.{hour}.nc'],
                              topo_file=os.environ['TOPO'], grid_dir='grids', map_dir='maps',
                              tmp_dir=tmp, verbose=True, check_input_files=True)
if kind == 'fv2se':
    h.create_src_grid_file()
    h.create_dst_grid_file()
    h.create_map_file()
else:
    h.map_file = os.environ['MAP_FILE']
print('map file:', h.map_file)
fd = h.get_multifile_dict()
h.remap_horizontal_multifile(fd)
h.rename_vars_multifile(file_dict=fd)
h.add_time_date_variables_multifile(file_dict=fd)
h.surface_adjustment_multifile(file_dict=fd)
h.remap_vertical_multifile(file_dict=fd, vert_file_name=f'{hiccup_root}/files_vert/L128_for_E3SMv4_c20260820.nc')
h.atmos_state_adjustment_multifile(file_dict=fd)
h.combine_files(file_dict=fd, delete_files=True, output_file_name=out)
h.clean_global_attributes(file_name=out)
print('output:', out)
h.print_timer_summary()
