#!/usr/bin/env python
# ==============================================================================
# EAMxx initial condition from a reanalysis (ERA5, IFS, MERRA-2) on an np4
# (GLL) grid, in one pass.
#
#   make_ic.py init  --out IC.nc [options]   create the output file, freeze config
#   make_ic.py run   --out IC.nc [--task i --ntasks n]
#                                            fill columns (tasks run concurrently)
#   make_ic.py check --out IC.nc [--nsample N]
#                                            validate sampled columns
#
# Destination columns and model surface geopotential come from the
# topography file (lat_d, lon_d, PHIS_d on ncol_d): EAMxx reads phis from
# PHIS_d at run time, so ps is adjusted to exactly that surface, and the
# IC's ncol order is the topography file's. Methods: see kernels.py and
# README.md.
# ==============================================================================
import argparse, datetime, glob, json, os, subprocess, sys, time
import numpy as np
import netCDF4 as nc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kernels as K
import sources
from cdf5 import ColumnWriter

THREE_D = ['T_mid', 'U', 'V', 'qv', 'qc', 'qi', 'o3_volume_mix_ratio']
TRACERS = [('clwc', 'qc'), ('ciwc', 'qi'), ('o3', 'o3_volume_mix_ratio')]


def status_dir(out):
    return out + '.status'


def load_config(out):
    return json.load(open(os.path.join(status_dir(out), 'config.json')))


def git_rev():
    d = os.path.dirname(os.path.abspath(__file__))
    try:
        rev = subprocess.run(['git', '-C', d, 'rev-parse', '--short', 'HEAD'],
                             capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(['git', '-C', d, 'status', '--porcelain', '.'],
                               capture_output=True, text=True).stdout.strip()
        return rev + ('-dirty' if dirty else '')
    except OSError:
        return 'unknown'


# ------------------------------------------------------------------------------
def cmd_init(a):
    out = a.out
    if os.path.exists(out) and not a.force:
        sys.exit(f'{out} exists (use --force to overwrite)')
    inputs = [a.atm] + ([a.sfc] if a.sfc else []) + ([a.ab] if a.ab else [])
    for f in inputs + [a.topo, a.vert]:
        if not os.path.isfile(f):
            sys.exit(f'missing input: {f}')
    t = nc.Dataset(a.topo)
    ncol = len(t.dimensions['ncol_d'])
    v = nc.Dataset(a.vert)
    nlev = len(v.dimensions['lev'])
    init_time = datetime.datetime.strptime(f'{a.date} {a.hour}', '%Y-%m-%d %H')

    cfg = dict(vars(a))
    cfg.pop('func', None)
    cfg.update(ncol=ncol, nlev=nlev, tool_rev=git_rev(),
               created=datetime.datetime.now().isoformat(timespec='seconds'))

    o = nc.Dataset(out, 'w', format='NETCDF3_64BIT_DATA')
    o.set_fill_off()
    o.createDimension('time', None)
    o.createDimension('ncol', ncol)
    o.createDimension('lev', nlev)
    o.createDimension('ilev', nlev + 1)

    def var(name, dt, dims, units, long_name):
        x = o.createVariable(name, dt, dims)
        x.units, x.long_name = units, long_name
        return x

    meta = {
        'T_mid': ('K', 'temperature'),
        'U': ('m/s', 'zonal wind'),
        'V': ('m/s', 'meridional wind'),
        'qv': ('kg/kg', 'water vapor wet mixing ratio (specific humidity)'),
        'qc': ('kg/kg', 'cloud liquid wet mixing ratio'),
        'qi': ('kg/kg', 'cloud ice wet mixing ratio' + (' (ice + snow where available)' if a.snow_to_ice else '')),
        'o3_volume_mix_ratio': ('mol/mol', 'ozone volume mixing ratio'),
    }
    for name in THREE_D:
        var(name, 'f4', ('time', 'ncol', 'lev'), *meta[name])
    var('ps', 'f8', ('time', 'ncol'), 'Pa', 'surface pressure (on PHIS_d)')
    var('phis', 'f8', ('time', 'ncol'), 'm2/s2', 'surface geopotential (PHIS_d of the topography file)')
    var('lat', 'f8', ('ncol',), 'degrees_north', 'latitude')
    var('lon', 'f8', ('ncol',), 'degrees_east', 'longitude')
    for name in ['hyam', 'hybm']:
        var(name, 'f8', ('lev',), '1', v[name].long_name if 'long_name' in v[name].ncattrs() else name)
    for name in ['hyai', 'hybi']:
        var(name, 'f8', ('ilev',), '1', v[name].long_name if 'long_name' in v[name].ncattrs() else name)
    var('lev', 'f8', ('lev',), 'level', 'hybrid level at midpoints')
    var('ilev', 'f8', ('ilev',), 'level', 'hybrid level at interfaces')
    var('P0', 'f8', (), 'Pa', 'reference pressure')
    tv = var('time', 'f8', ('time',), f'days since {init_time:%Y-%m-%d %H:%M:%S}', 'time')
    tv.calendar = 'noleap'
    var('date', 'i4', ('time',), '1', 'current date (YYYYMMDD)')
    var('datesec', 'i4', ('time',), 's', 'current seconds of current date')

    o.title = 'EAMxx initial condition from reanalysis'
    o.source = (f'{a.source} '
                f'{init_time:%Y-%m-%d %HZ}')
    o.method = (f'horizontal {a.horiz} along source levels (moisture/condensate/ozone limited '
                'to local 2x2 range; winds as 3D vectors); ps adjusted to PHIS_d by '
                'hypsometric interpolation within the source column (lapse-rate '
                'extrapolation below the source surface); T linear in ln p; U,V linear in ln p '
                + (f'at terrain-following lookup pressures blending to pressure matching over '
                   f'{a.wind_tf_depth / 100:g} hPa above the surface' if a.wind_tf_depth > 0
                   else 'by pressure matching') + '; q and '
                'tracers mass-conserving PLM remap; supersaturation (liquid, '
                'Murphy-Koop) removed')
    o.input_files = ', '.join(inputs
                              + [a.topo, a.vert])
    o.tool = f'eamxx-reanalysis-ic make_ic.py rev {cfg["tool_rev"]}'
    o.history = f'{cfg["created"]}: created'

    o['lat'][:] = t['lat_d'][:]
    o['lon'][:] = t['lon_d'][:]
    for name in ['hyam', 'hybm', 'hyai', 'hybi', 'lev', 'ilev']:
        o[name][:] = v[name][:]
    o['P0'][...] = float(v['P0'][...]) if 'P0' in v.variables else 1.0e5
    o['time'][0] = 0.0
    o['date'][0] = int(f'{init_time:%Y%m%d}')
    o['datesec'][0] = init_time.hour * 3600
    o.close()

    os.makedirs(status_dir(out), exist_ok=True)
    for f in glob.glob(os.path.join(status_dir(out), '*.done')):
        os.remove(f)
    json.dump(cfg, open(os.path.join(status_dir(out), 'config.json'), 'w'), indent=2)

    # writer sanity check: header layout readable, ncol-major variables
    w = ColumnWriter(out)
    assert w.numrecs == 1, 'expected one record'
    w.close()
    print(f'initialized {out}: ncol={ncol} nlev={nlev}')


# ------------------------------------------------------------------------------
def load_source(cfg):
    fields = ['t', 'q', 'u', 'v', 'clwc', 'ciwc', 'o3'] + (['cswc'] if cfg['snow_to_ice'] else [])
    src = sources.read_source(cfg['source'], cfg['atm'], cfg['sfc'], cfg['ab'], fields, cfg['hour'])
    missing = [f for f in ['t', 'q', 'u', 'v', 'clwc', 'ciwc', 'o3'] if f not in src.f3d]
    if missing:
        raise ValueError(f'missing source fields: {missing}')
    if cfg['snow_to_ice']:
        if 'cswc' in src.f3d:
            src.f3d['ciwc'] = src.f3d['ciwc'] + src.f3d.pop('cswc')
        else:
            print('note: no cswc in source; qi is cloud ice only')
    return src


def process_chunk(src, vert, lat, lon, phis, cubic, wind_tf_depth):
    jj, ii, wy, wx = K.horiz_stencil(lat, lon, float(src.lat[0]), float(src.lat[1] - src.lat[0]),
                                     src.lat.size, float(src.lon[0]), float(src.lon[1] - src.lon[0]),
                                     src.lon.size, cubic)
    n = lat.size
    nsrc = src.a_full.size

    def scalar(f, clip):
        out = np.empty((n, f.shape[2]))
        K.interp_scalar(f, jj, ii, wy, wx, clip, out)
        return out

    ps_e = np.exp(scalar(src.lnps, False)[:, 0])
    zs_e = scalar(src.zs, False)[:, 0]
    T_s = scalar(src.f3d['t'], False)
    q_s = scalar(src.f3d['q'], True)
    u_s = np.empty((n, nsrc))
    v_s = np.empty((n, nsrc))
    K.interp_wind(src.f3d['u'], src.f3d['v'], src.lat.astype(np.float64), src.lon.astype(np.float64),
                  lat, lon, jj, ii, wy, wx, u_s, v_s)
    trc_s = np.empty((len(TRACERS), n, nsrc))
    for k, (f, _) in enumerate(TRACERS):
        K.interp_scalar(src.f3d[f], jj, ii, wy, wx, True, trc_s[k])

    nt = vert['hyam'].size
    T_o = np.empty((n, nt)); q_o = np.empty((n, nt))
    u_o = np.empty((n, nt)); v_o = np.empty((n, nt))
    trc_o = np.empty((len(TRACERS), n, nt))
    ps_o = np.empty(n)
    diag = np.empty((n, 3))
    K.column_kernel(src.is_ml, src.a_full, src.b_full, src.a_half, src.b_half,
                    ps_e, zs_e, phis, T_s, q_s, u_s, v_s, trc_s,
                    vert['hyam'], vert['hybm'], vert['hyai'], vert['hybi'], vert['P0'], wind_tf_depth,
                    T_o, q_o, u_o, v_o, trc_o, ps_o, diag)
    out = {'T_mid': T_o, 'U': u_o, 'V': v_o, 'qv': q_o, 'ps': ps_o}
    for k, (_, name) in enumerate(TRACERS):
        out[name] = trc_o[k]
    out['o3_volume_mix_ratio'] *= K.MWDRY / K.MWO3          # mass -> volume mixing ratio
    return out, diag, ps_e


def cmd_run(a):
    cfg = load_config(a.out)
    ncol, chunk = cfg['ncol'], cfg['chunk']
    task = int(os.environ.get('SLURM_PROCID', 0)) if a.task is None else a.task
    ntasks = int(os.environ.get('SLURM_NTASKS', 1)) if a.ntasks is None else a.ntasks
    # contiguous ranges of whole chunks per task
    chunks = [(c, min(c + chunk, ncol)) for c in range(0, ncol, chunk)]
    mine = chunks[task::ntasks]
    sd = status_dir(a.out)
    todo = [c for c in mine if not os.path.exists(os.path.join(sd, f'c{c[0]:012d}.done'))]
    print(f'task {task}/{ntasks}: {len(mine)} chunks, {len(todo)} to do', flush=True)
    if not todo:
        return
    t0 = time.time()
    src = load_source(cfg)
    v = nc.Dataset(cfg['vert'])
    vert = {k: np.asarray(v[k][:], np.float64) for k in ['hyam', 'hybm', 'hyai', 'hybi']}
    vert['P0'] = float(v['P0'][...]) if 'P0' in v.variables else 1.0e5
    topo = nc.Dataset(cfg['topo'])
    w = ColumnWriter(a.out)
    print(f'task {task}: source loaded in {time.time() - t0:.0f} s', flush=True)
    for c0, c1 in todo:
        t1 = time.time()
        lat = np.asarray(topo['lat_d'][c0:c1], np.float64)
        lon = np.asarray(topo['lon_d'][c0:c1], np.float64)
        phis = np.asarray(topo['PHIS_d'][c0:c1], np.float64)
        if not (np.isfinite(lat).all() and np.isfinite(lon).all() and np.isfinite(phis).all()):
            raise ValueError(f'non-finite topography/coordinates in columns {c0}:{c1}')
        out, diag, ps_e = process_chunk(src, vert, lat, lon, phis, cfg['horiz'] == 'bicubic',
                                        float(cfg.get('wind_tf_depth', 0.0)))
        for name, arr in out.items():
            if not np.isfinite(arr).all():
                raise ValueError(f'non-finite {name} in columns {c0}:{c1}')
        t2 = time.time()
        for name, arr in out.items():
            w.write(name, c0, arr)
        w.write('phis', c0, phis)
        open(os.path.join(sd, f'c{c0:012d}.done'), 'w').write(
            json.dumps(dict(dz_min=float(diag[:, 0].min()), dz_max=float(diag[:, 0].max()),
                            removed_max=float(diag[:, 1].max()),
                            removed_mean=float(diag[:, 1].mean()),
                            ps_min=float(out['ps'].min()), ps_max=float(out['ps'].max()),
                            dps_max=float(np.abs(out['ps'] - ps_e).max()))))
        print(f'task {task}: cols {c0}:{c1} compute {t2 - t1:.1f} s write {time.time() - t2:.1f} s; '
              f'dz [{diag[:, 0].min():.0f},{diag[:, 0].max():.0f}] m, '
              f'qv removed max {diag[:, 1].max():.3f} kg/m2', flush=True)
    w.close()
    print(f'task {task}: done in {time.time() - t0:.0f} s', flush=True)


# ------------------------------------------------------------------------------
def cmd_check(a):
    """Validate sampled columns: completeness, finite values, ranges,
    positivity, saturation, and hydrostatic consistency (z500 recomputed from
    ps, T, qv and PHIS_d against the analysed z500 of the source)."""
    cfg = load_config(a.out)
    ncol = cfg['ncol']
    sd = status_dir(a.out)
    chunks = list(range(0, ncol, cfg['chunk']))
    missing = [c for c in chunks if not os.path.exists(os.path.join(sd, f'c{c:012d}.done'))]
    print(f'chunks: {len(chunks) - len(missing)}/{len(chunks)} done')
    if missing:
        print(f'  missing chunk starts (first 10): {missing[:10]}')
    rng = np.random.default_rng(0)
    idx = np.sort(rng.choice(ncol, min(a.nsample, ncol), replace=False))
    done = np.array([os.path.exists(os.path.join(sd, f'c{(i // cfg["chunk"]) * cfg["chunk"]:012d}.done')) for i in idx])
    idx = idx[done]
    o = nc.Dataset(a.out)
    get = lambda n: np.asarray(o[n][0, idx] if o[n].dimensions[0] == 'time' else o[n][idx], np.float64)
    d = {n: get(n) for n in THREE_D + ['ps', 'phis', 'lat', 'lon']}
    ok = True
    print(f'{idx.size} sampled columns')
    for n in THREE_D + ['ps']:
        x = d[n]
        fin = np.isfinite(x).all()
        ok &= fin
        print(f'  {n:22s} min {np.nanmin(x):12.5g} max {np.nanmax(x):12.5g} finite {fin}')
    for n in ['qv', 'qc', 'qi', 'o3_volume_mix_ratio']:
        if (d[n] < 0).any():
            ok = False
            print(f'  FAIL: negative {n}')
    hyam, hybm = o['hyam'][:], o['hybm'][:]
    hyai, hybi = o['hyai'][:], o['hybi'][:]
    P0 = float(o['P0'][...])
    pm = hyam[None, :] * P0 + hybm[None, :] * d['ps'][:, None]
    pi = hyai[None, :] * P0 + hybi[None, :] * d['ps'][:, None]
    qs = np.vectorize(K.qsat_liq)(d['T_mid'], pm)
    ss = (d['qv'] > qs * (1 + 1e-5)).sum()
    print(f'  supersaturated points (liquid): {ss}')
    ok &= ss == 0
    # topography consistency with the topo file
    t = nc.Dataset(cfg['topo'])
    phis_t = np.asarray(t['PHIS_d'][idx], np.float64)
    lat_t = np.asarray(t['lat_d'][idx], np.float64)
    print(f'  max |phis - PHIS_d| {np.abs(d["phis"] - phis_t).max():.3g}, max |lat - lat_d| {np.abs(d["lat"] - lat_t).max():.3g}')
    # hydrostatic check against the source's own analysed 500 hPa height
    # (pressure-level file: ERA5 'z' geopotential or MERRA-2 'H' height)
    if a.ref_pl:
        Tv = d['T_mid'] * (1 + K.ZVIR * d['qv'])
        phi_i = np.empty(pi.shape)
        phi_i[:, -1] = d['phis']
        for k in range(pm.shape[1] - 1, -1, -1):
            phi_i[:, k] = phi_i[:, k + 1] + K.RD * Tv[:, k] * np.log(pi[:, k + 1] / pi[:, k])
        z500 = np.array([np.interp(np.log(5e4), np.log(pi[c]), phi_i[c]) for c in range(idx.size)]) / K.G
        e = nc.Dataset(a.ref_pl)
        levname = 'pressure_level' if 'pressure_level' in e.variables else 'lev'
        latname = 'latitude' if 'latitude' in e.variables else 'lat'
        lonname = 'longitude' if 'longitude' in e.variables else 'lon'
        k500 = int(np.where(np.isclose(e[levname][:], 500))[0][0])
        it = sources._time_index(e, cfg['hour'])
        zname = 'z' if 'z' in e.variables else 'H'
        zf = np.ma.filled(np.ma.asarray(e[zname][it, k500]).astype(np.float64), np.nan)
        if zname == 'z':
            zf /= K.G                                     # geopotential -> height
        elat, elon = e[latname][:].data, e[lonname][:].data
        jj, ii, wy, wx = K.horiz_stencil(d['lat'], d['lon'], float(elat[0]), float(elat[1] - elat[0]),
                                         elat.size, float(elon[0]), float(elon[1] - elon[0]), elon.size, False)
        ze = np.empty((idx.size, 1))
        K.interp_scalar(np.ascontiguousarray(zf[:, :, None].astype(np.float32)), jj, ii, wy, wx, False, ze)
        dz = z500 - ze[:, 0]
        # only where 500 hPa is well above the surface (closer to the ground
        # the analysed z500 is itself extrapolated)
        valid = (pi[:, -1] > 7.0e4) & np.isfinite(dz)
        print(f'  z500 (recomputed - analysed): mean {dz[valid].mean():.2f} m, std {dz[valid].std():.2f} m, '
              f'max |.| {np.abs(dz[valid]).max():.1f} m ({valid.sum()} columns with ps > 700 hPa)')
        ok &= abs(dz[valid].mean()) < 5 and dz[valid].std() < 10
    print('CHECK PASSED' if ok else 'CHECK FAILED')
    sys.exit(0 if ok else 1)


# ------------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest='cmd', required=True)
    i = sp.add_parser('init')
    i.add_argument('--out', required=True)
    i.add_argument('--source', choices=sources.SOURCES, required=True,
                   help='source and level type (model levels preferred)')
    i.add_argument('--atm', required=True, help='3D fields (netCDF); MERRA-2: the whole file')
    i.add_argument('--sfc', help='era5/ifs-ml: lnsp and z on level 1; era5-pl: sp and z')
    i.add_argument('--ab', help='era5/ifs-ml: half-level a [Pa] b (text, from GRIB pv)')
    i.add_argument('--topo', required=True, help='topography file with lat_d, lon_d, PHIS_d')
    i.add_argument('--vert', required=True, help='vertical grid file (hyam, hybm, hyai, hybi, P0)')
    i.add_argument('--date', required=True, help='YYYY-MM-DD')
    i.add_argument('--hour', required=True, type=int)
    i.add_argument('--horiz', choices=['bicubic', 'bilinear'], default='bicubic')
    i.add_argument('--wind-tf-depth', type=float, default=15000.0,
                   help='U/V: depth [Pa] over which the vertical lookup blends from terrain-following '
                        '(at the surface) to pressure matching; 0 = pressure matching (default 15000)')
    i.add_argument('--no-snow-to-ice', dest='snow_to_ice', action='store_false',
                   help='do not add snow (ERA5/IFS cswc) to cloud ice')
    i.add_argument('--chunk', type=int, default=1_000_000, help='columns per work unit')
    i.add_argument('--force', action='store_true')
    i.set_defaults(func=cmd_init)
    r = sp.add_parser('run')
    r.add_argument('--out', required=True)
    r.add_argument('--task', type=int, help='default: SLURM_PROCID or 0')
    r.add_argument('--ntasks', type=int, help='default: SLURM_NTASKS or 1')
    r.set_defaults(func=cmd_run)
    c = sp.add_parser('check')
    c.add_argument('--out', required=True)
    c.add_argument('--nsample', type=int, default=20000)
    c.add_argument('--ref-pl', help='pressure-level file of the same analysis with z (ERA5) or H\n'
                   '(MERRA-2) at 500 hPa, for the hydrostatic check')
    c.set_defaults(func=cmd_check)
    a = p.parse_args()
    if a.cmd == 'init' and a.source in ('era5-ml', 'ifs-ml') and not (a.ab and a.sfc):
        p.error(f'--sfc and --ab are required with --source {a.source}')
    if a.cmd == 'init' and a.source == 'era5-pl' and not a.sfc:
        p.error('--sfc is required with --source era5-pl')
    a.func(a)


if __name__ == '__main__':
    main()
