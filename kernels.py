"""
Numerical kernels for building EAMxx initial conditions from ERA5.

Two stages, both parallel over destination columns (numba prange):
  1. Horizontal: interpolate ERA5 (regular lat-lon) to destination points
     along ERA5 levels (model levels follow the terrain).
  2. Column: rebuild the ERA5 column, adjust surface pressure to the model
     topography, remap to the target hybrid levels, adjust the state.

Physical constants are EAMxx's (components/eamxx/src/share/physics/
physics_constants.hpp), so the IC is hydrostatically consistent with the
model's own equation of state and saturation formula.
"""
import math
import numpy as np
from numba import njit, prange

# EAMxx constants
RD    = 287.042          # dry air gas constant [J/kg/K]
RV    = 461.505          # water vapour gas constant [J/kg/K]
G     = 9.80616          # gravity [m/s2]
MWDRY = 28.966           # dry air molar mass [g/mol]
MWH2O = 18.016           # water molar mass [g/mol]
MWO3  = 47.9982          # ozone molar mass [g/mol]
EP2   = MWH2O / MWDRY
ZVIR  = RV / RD - 1.0    # Tv = T*(1 + ZVIR*q), q = specific humidity

# Below-ground extrapolation (Trenberth et al. 1993, as used by ECMWF/CAM)
GAMMA_STD   = 0.0065     # standard lapse rate [K/m]
T_WARM_CAP  = 290.5      # [K] limit extrapolated virtual temperature

QV_MIN = 1.0e-12         # floor for water vapour [kg/kg]


# ------------------------------------------------------------------------------
# Horizontal interpolation
# ------------------------------------------------------------------------------
@njit(cache=True)
def _cubic_weights(t, w):
    """Keys (a=-0.5, Catmull-Rom) cubic convolution weights for points
    -1, 0, 1, 2 at fractional position t in [0,1]. C1-continuous, reproduces
    quadratics, weights sum to 1."""
    t2 = t * t
    t3 = t2 * t
    w[0] = 0.5 * (-t3 + 2.0 * t2 - t)
    w[1] = 0.5 * (3.0 * t3 - 5.0 * t2 + 2.0)
    w[2] = 0.5 * (-3.0 * t3 + 4.0 * t2 + t)
    w[3] = 0.5 * (t3 - t2)


@njit(parallel=True, cache=True)
def horiz_stencil(lat, lon, lat0, dlat, nlat, lon0, dlon, nlon, cubic):
    """4x4 stencil indices and separable weights on a regular lat-lon grid
    (latitudes lat0 + j*dlat, longitudes lon0 + i*dlon, global in longitude).
    Bilinear uses the inner 2x2 (outer weights zero). Rows beyond the poles
    are clamped to the pole row."""
    n = lat.size
    jj = np.empty((n, 4), np.int64)
    ii = np.empty((n, 4), np.int64)
    wy = np.zeros((n, 4))
    wx = np.zeros((n, 4))
    for c in prange(n):
        y = (lat[c] - lat0) / dlat
        j0 = int(math.floor(y))
        if j0 < 0:
            j0 = 0
        if j0 > nlat - 2:
            j0 = nlat - 2
        ty = y - j0
        x = ((lon[c] - lon0) % 360.0) / dlon
        i0 = int(math.floor(x))
        tx = x - i0
        if i0 >= nlon:
            i0 -= nlon
        for k in range(4):
            j = j0 - 1 + k
            jj[c, k] = min(max(j, 0), nlat - 1)
            ii[c, k] = (i0 - 1 + k + nlon) % nlon
        if cubic:
            _cubic_weights(ty, wy[c])
            _cubic_weights(tx, wx[c])
        else:
            wy[c, 1] = 1.0 - ty
            wy[c, 2] = ty
            wx[c, 1] = 1.0 - tx
            wx[c, 2] = tx
    return jj, ii, wy, wx


@njit(parallel=True, cache=True)
def interp_scalar(f, jj, ii, wy, wx, clip, out):
    """Interpolate f[nlat, nlon, nl] to columns: out[ncol, nl].
    clip: limit to the range of the surrounding 2x2 source points, so the
    cubic cannot create new extrema (used for moisture, condensate, ozone)."""
    n = jj.shape[0]
    nl = f.shape[2]
    for c in prange(n):
        acc = np.zeros(nl)
        for a in range(4):
            if wy[c, a] == 0.0:
                continue
            for b in range(4):
                w = wy[c, a] * wx[c, b]
                if w == 0.0:
                    continue
                row = f[jj[c, a], ii[c, b]]
                for k in range(nl):
                    acc[k] += w * row[k]
        if clip:
            r11 = f[jj[c, 1], ii[c, 1]]
            r12 = f[jj[c, 1], ii[c, 2]]
            r21 = f[jj[c, 2], ii[c, 1]]
            r22 = f[jj[c, 2], ii[c, 2]]
            for k in range(nl):
                lo = min(min(r11[k], r12[k]), min(r21[k], r22[k]))
                hi = max(max(r11[k], r12[k]), max(r21[k], r22[k]))
                acc[k] = min(max(acc[k], lo), hi)
        for k in range(nl):
            out[c, k] = acc[k]


@njit(parallel=True, cache=True)
def interp_wind(u, v, slat, slon, dlat_pts, dlon_pts, jj, ii, wy, wx, uo, vo):
    """Interpolate horizontal wind as a 3D Cartesian vector: each source
    (u,v) is expressed as u*east + v*north at its own location, the vectors
    are interpolated, and the result is projected onto the local east/north
    unit vectors at the destination. Correct everywhere, including near and
    across the poles, unlike interpolating u and v as scalars."""
    n = jj.shape[0]
    nl = u.shape[2]
    d2r = math.pi / 180.0
    for c in prange(n):
        X = np.zeros(nl)
        Y = np.zeros(nl)
        Z = np.zeros(nl)
        for a in range(4):
            if wy[c, a] == 0.0:
                continue
            phi = slat[jj[c, a]] * d2r
            sphi = math.sin(phi)
            cphi = math.cos(phi)
            for b in range(4):
                w = wy[c, a] * wx[c, b]
                if w == 0.0:
                    continue
                lam = slon[ii[c, b]] * d2r
                slam = math.sin(lam)
                clam = math.cos(lam)
                ur = u[jj[c, a], ii[c, b]]
                vr = v[jj[c, a], ii[c, b]]
                for k in range(nl):
                    # east = (-slam, clam, 0); north = (-sphi*clam, -sphi*slam, cphi)
                    X[k] += w * (-slam * ur[k] - sphi * clam * vr[k])
                    Y[k] += w * (clam * ur[k] - sphi * slam * vr[k])
                    Z[k] += w * (cphi * vr[k])
        phi = dlat_pts[c] * d2r
        lam = dlon_pts[c] * d2r
        sphi = math.sin(phi)
        cphi = math.cos(phi)
        slam = math.sin(lam)
        clam = math.cos(lam)
        for k in range(nl):
            uo[c, k] = -slam * X[k] + clam * Y[k]
            vo[c, k] = -sphi * clam * X[k] - sphi * slam * Y[k] + cphi * Z[k]


# ------------------------------------------------------------------------------
# Column physics
# ------------------------------------------------------------------------------
@njit(cache=True)
def svp_liq(T):
    """Saturation vapour pressure over liquid [Pa], Murphy & Koop (2005)
    eq. 10, as in EAMxx MurphyKoop_svp (EAMxx's default)."""
    lt = math.log(T)
    return math.exp(54.842763 - 6763.22 / T - 4.210 * lt + 0.000367 * T
                    + math.tanh(0.0415 * (T - 218.8))
                    * (53.878 - 1331.22 / T - 9.44523 * lt + 0.014025 * T))


@njit(cache=True)
def qsat_liq(T, p):
    """Saturation specific humidity over liquid [kg/kg]. Returns 1 where
    saturation cannot be reached (e comparable to p, upper atmosphere)."""
    e = svp_liq(T)
    den = p - (1.0 - EP2) * e
    if den <= EP2 * e:
        return 1.0
    return EP2 * e / den


@njit(cache=True)
def remap_plm(e, q, m, pt, out):
    """Mass-conserving remap of layer means q[0:m] on source interfaces
    e[0:m+1] (pressure, increasing downward) to target interfaces pt.
    Piecewise-linear reconstruction with slopes limited so each layer's edge
    values stay within the range of its neighbours' means: conserves the
    column integral, adds no new extrema, keeps non-negative fields
    non-negative. Target interfaces must lie within [e[0], e[m]]."""
    s = np.zeros(m)
    for i in range(1, m - 1):
        pcm = 0.5 * (e[i - 1] + e[i])
        pcp = 0.5 * (e[i + 1] + e[i + 2])
        dp = e[i + 1] - e[i]
        if pcp <= pcm or dp <= 0.0:
            continue
        sl = (q[i + 1] - q[i - 1]) / (pcp - pcm)
        qmax = max(max(q[i - 1], q[i]), q[i + 1])
        qmin = min(min(q[i - 1], q[i]), q[i + 1])
        lim = min(qmax - q[i], q[i] - qmin)
        if 0.5 * dp * abs(sl) > lim:
            sl = math.copysign(2.0 * lim / dp, sl)
        s[i] = sl
    C = np.empty(m + 1)
    C[0] = 0.0
    for i in range(m):
        C[i + 1] = C[i] + q[i] * (e[i + 1] - e[i])
    nt = pt.size - 1
    i = 0
    cprev = 0.0
    for kt in range(nt + 1):
        p = pt[kt]
        if p <= e[0]:
            cum = q[0] * (p - e[0])
        elif p >= e[m]:
            cum = C[m] + q[m - 1] * (p - e[m])
        else:
            while e[i + 1] < p:
                i += 1
            pc = 0.5 * (e[i] + e[i + 1])
            cum = (C[i] + q[i] * (p - e[i])
                   + 0.5 * s[i] * ((p - pc) ** 2 - (e[i] - pc) ** 2))
        if kt > 0:
            out[kt - 1] = (cum - cprev) / (pt[kt] - pt[kt - 1])
        cprev = cum


@njit(cache=True)
def _interp_lnp(pn, fn, nn, pt, out, fbelow_lapse, Ts, ps, rgam):
    """Linear-in-ln(p) interpolation from nodes pn[0:nn] (increasing) with
    values fn to target pressures pt (increasing). Above the top node: the top
    value. Below the bottom node (= ERA5 surface): if fbelow_lapse, the
    lapse-rate profile Ts*(p/ps)**rgam, else the bottom value."""
    k = 0
    for kt in range(pt.size):
        p = pt[kt]
        if p <= pn[0]:
            out[kt] = fn[0]
        elif p > pn[nn - 1]:
            if fbelow_lapse:
                out[kt] = Ts * (p / ps) ** rgam
            else:
                out[kt] = fn[nn - 1]
        else:
            while pn[k + 1] < p:
                k += 1
            f = (math.log(p) - math.log(pn[k])) / (math.log(pn[k + 1]) - math.log(pn[k]))
            out[kt] = fn[k] + f * (fn[k + 1] - fn[k])


@njit(cache=True)
def _interp_lnp_any(pn, fn, nn, pt, out):
    """Like _interp_lnp without the lapse-rate option, for target pressures in
    any order (bisection per target). Outside [pn[0], pn[nn-1]]: end values."""
    for kt in range(pt.size):
        p = pt[kt]
        if p <= pn[0]:
            out[kt] = fn[0]
        elif p >= pn[nn - 1]:
            out[kt] = fn[nn - 1]
        else:
            lo, hi = 0, nn - 1
            while hi - lo > 1:
                mid = (lo + hi) // 2
                if pn[mid] < p:
                    lo = mid
                else:
                    hi = mid
            f = (math.log(p) - math.log(pn[lo])) / (math.log(pn[hi]) - math.log(pn[lo]))
            out[kt] = fn[lo] + f * (fn[hi] - fn[lo])


@njit(parallel=True, cache=True)
def column_kernel(is_ml, a_full, b_full, a_half, b_half,
                  ps_e, zs_e, phis_m, T_s, q_s, u_s, v_s, trc_s,
                  hyam, hybm, hyai, hybi, P0, wind_tf_depth,
                  T_o, q_o, u_o, v_o, trc_o, ps_o, diag):
    """Per destination column:
      - ERA5 column: full-level pressures p = a + b*ps (model levels) or the
        fixed pressure levels above the ERA5 surface (pressure levels);
        interfaces from a_half/b_half (model levels) or level midpoints.
      - Geopotential of each level by hypsometric integration upward from the
        ERA5 surface geopotential with virtual temperature.
      - Model surface pressure ps_m on the model surface geopotential:
          model surface above ERA5 surface: ln(p) interpolated in geopotential
          within the ERA5 column (no assumed lapse rate);
          below: extrapolated with the standard lapse rate from the ERA5
          surface virtual temperature, capped at 290.5 K (Trenberth et al. 1993).
      - Remap to target levels p = hyam*P0 + hybm*ps_m:
          T linear in ln(p); below the ERA5 surface it follows the same
          lapse rate as the ps extrapolation;
          u, v linear in ln(p) at a lookup pressure that is terrain-following
          near the ground and blends to the target pressure with height:
            p_look = pm * (1 + w * (ps/ps_m - 1)),
            w = max(0, 1 - (ps_m - pm) / wind_tf_depth),
          so the lowest model level takes the source wind at the same sigma
          (about the same height above the source surface) instead of the
          same pressure. With mismatched terrain, matching by pressure gives
          ridges above the source surface free-atmosphere winds and valleys
          below it the held-constant lowest source wind. Temperature keeps
          pressure matching so ps and T stay hydrostatically consistent.
          wind_tf_depth <= 0: plain pressure matching, u/v held constant below
          the source surface;
          q and tracers by mass-conserving PLM remap (constant below the
          ERA5 surface).
      - Remove supersaturation with respect to liquid (EAMxx's saturation
        formula; ice supersaturation up to liquid saturation is allowed, as in
        P3), floor q at QV_MIN.
    diag[:,0] = ERA5 minus model surface height [m] (>0: model surface lower)
    diag[:,1] = water vapour removed by the supersaturation limit [kg/m2]
    diag[:,2] = number of ERA5 levels used
    """
    ncol = ps_e.size
    nsrc = a_full.size
    ntr = trc_s.shape[0]
    nt = hyam.size
    rgam_std = RD * GAMMA_STD / G
    for c in prange(ncol):
        ps = ps_e[c]
        zs = zs_e[c]
        phm = phis_m[c]

        # --- ERA5 column (levels above the ERA5 surface) ---
        p = np.empty(nsrc)
        n = 0
        for k in range(nsrc):
            pk = a_full[k] + b_full[k] * ps
            if pk < ps:
                p[n] = pk
                n += 1
            else:
                break
        e = np.empty(n + 2)          # interfaces (+1 spare for extension)
        if is_ml:
            for k in range(n + 1):
                e[k] = a_half[k] + b_half[k] * ps
        else:
            e[0] = 0.0
            for k in range(1, n):
                e[k] = 0.5 * (p[k - 1] + p[k])
            e[n] = ps

        Tv = np.empty(n)
        for k in range(n):
            Tv[k] = T_s[c, k] * (1.0 + ZVIR * q_s[c, k])
        pL = p[n - 1]
        TvS = Tv[n - 1] * (ps / pL) ** rgam_std    # virtual T at ERA5 surface
        TS = T_s[c, n - 1] * (ps / pL) ** rgam_std # T at ERA5 surface

        phi = np.empty(n)
        phi[n - 1] = zs + RD * 0.5 * (TvS + Tv[n - 1]) * math.log(ps / pL)
        for k in range(n - 2, -1, -1):
            phi[k] = phi[k + 1] + RD * 0.5 * (Tv[k] + Tv[k + 1]) * math.log(p[k + 1] / p[k])

        # --- surface pressure on the model topography ---
        dz = (zs - phm) / G
        rgam = rgam_std
        if phm >= zs:
            plow = ps
            philow = zs
            psm = p[0]
            for k in range(n - 1, -1, -1):
                if phi[k] >= phm:
                    f = (phm - philow) / (phi[k] - philow)
                    psm = math.exp(math.log(plow) + f * (math.log(p[k]) - math.log(plow)))
                    break
                plow = p[k]
                philow = phi[k]
        else:
            # Extrapolated virtual temperature Tv(z) = TvS + gam*(depth),
            # capped at T_WARM_CAP (or isothermal if already warmer). Unlike
            # Trenberth's sea-level-pressure recipe, Tstar is not averaged
            # toward the cap: the same profile is used for T below the ERA5
            # surface, so ps and the T profile stay hydrostatically consistent.
            gam = GAMMA_STD
            Tstar = TvS
            if TvS + gam * dz > T_WARM_CAP:
                if TvS <= T_WARM_CAP:
                    gam = (T_WARM_CAP - TvS) / dz
                else:
                    gam = 0.0
            if gam > 0.0:
                psm = ps * (1.0 + gam * dz / Tstar) ** (G / (RD * gam))
            else:
                psm = ps * math.exp(G * dz / (RD * Tstar))
            rgam = RD * gam / G
        ps_o[c] = psm

        # --- target levels ---
        pm = np.empty(nt)
        pi = np.empty(nt + 1)
        for k in range(nt):
            pm[k] = hyam[k] * P0 + hybm[k] * psm
        for k in range(nt + 1):
            pi[k] = hyai[k] * P0 + hybi[k] * psm

        # nodes for ln(p) interpolation: ERA5 levels + ERA5 surface
        pn = np.empty(n + 1)
        fn = np.empty(n + 1)
        for k in range(n):
            pn[k] = p[k]
        pn[n] = ps
        tmp = np.empty(nt)

        for k in range(n):
            fn[k] = T_s[c, k]
        fn[n] = TS
        _interp_lnp(pn, fn, n + 1, pm, tmp, True, TS, ps, rgam)
        for k in range(nt):
            T_o[c, k] = tmp[k]

        # winds: lookup pressures (terrain-following near the ground); nodes
        # are the source levels only, so the lowest level is the bottom value
        plook = np.empty(nt)
        for k in range(nt):
            w = 0.0
            if wind_tf_depth > 0.0:
                w = max(0.0, 1.0 - (psm - pm[k]) / wind_tf_depth)
            plook[k] = pm[k] * (1.0 + w * (ps / psm - 1.0))
        for k in range(n):
            fn[k] = u_s[c, k]
        _interp_lnp_any(pn, fn, n, plook, tmp)
        for k in range(nt):
            u_o[c, k] = tmp[k]
        for k in range(n):
            fn[k] = v_s[c, k]
        _interp_lnp_any(pn, fn, n, plook, tmp)
        for k in range(nt):
            v_o[c, k] = tmp[k]

        # --- mass-conserving remap of q and tracers ---
        m = n
        if psm > ps:                  # extend below the ERA5 surface
            e[n + 1] = psm
            m = n + 1
        qq = np.empty(m)
        for k in range(n):
            qq[k] = q_s[c, k]
        if m > n:
            qq[n] = q_s[c, n - 1]
        remap_plm(e, qq, m, pi, tmp)
        removed = 0.0
        for k in range(nt):
            qv = tmp[k]
            qs = qsat_liq(T_o[c, k], pm[k])
            if qv > qs:
                removed += (qv - qs) * (pi[k + 1] - pi[k]) / G
                qv = qs
            q_o[c, k] = max(qv, QV_MIN)
        for t in range(ntr):
            for k in range(n):
                qq[k] = trc_s[t, c, k]
            if m > n:
                qq[n] = trc_s[t, c, n - 1]
            remap_plm(e, qq, m, pi, tmp)
            for k in range(nt):
                trc_o[t, c, k] = max(tmp[k], 0.0)

        diag[c, 0] = dz
        diag[c, 1] = removed
        diag[c, 2] = n
