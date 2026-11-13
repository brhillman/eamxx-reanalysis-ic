# EAMxx initial conditions from ERA5

`make_ic.py` makes an EAMxx initial condition (IC) on an np4 (GLL) grid,
including regionally refined grids, directly from ERA5. It does this in one
pass, in parallel over columns. It replaces HICCUP for this purpose and does
not try to reproduce HICCUP's output.

## Why

HICCUP, as used for the CONUS x2/x3/x4 ICs, works like this:
- It interpolates horizontally on ERA5 pressure levels using a precomputed map
  file. The conservative maps gave blocky grid imprinting at km scales.
- It works on files one variable at a time, rewriting every file at every step.
  At x4 that meant more than a day on one node, more than 650 GB of temporary
  files and about 300 GB of memory, with no way to restart.

This tool instead:
- Reads ERA5 on its native **137 model levels** (pressure levels are supported
  as a fallback).
- Interpolates horizontally **along model levels** with weights computed
  directly from the regular lat-lon grid, so no map file is needed.
- Does all the column physics in memory and writes each column range straight
  into one output file.
- Restarts: finished chunks are skipped on a rerun.

## Method

1. **Horizontal**, from the ERA5 0.25° grid to each GLL node:
   - **Default**: bicubic (Keys/Catmull-Rom, smooth first derivatives) for T, ln ps and surface geopotential. Bilinear is an option.
   - **q, condensate and ozone**: the same interpolation, limited to the range of the surrounding 2×2 source points. This creates no new extremes and no negative values.
   - **Winds**: interpolated as 3D Cartesian vectors, then projected onto the local east and north directions. This is correct near and across the poles.
2. **ERA5 column**: full-level pressures `a + b·ps` and half levels from the L137 coefficients. Geopotential is integrated upward from ERA5's surface geopotential using virtual temperature. EAMxx's constants are used throughout.
3. **Surface pressure on the model topography** (`PHIS_d` in the topography file, which EAMxx reads at run time):
   - Where the model surface is above ERA5's, ln p is interpolated in geopotential within the ERA5 column. No lapse rate is assumed.
   - Where it is below, values are extrapolated with 6.5 K/km from the ERA5 surface virtual temperature, capped at 290.5 K as in Trenberth et al. (1993). The same profile gives T below the ERA5 surface, so ps and T are hydrostatically consistent.
4. **Vertical remap** to the target hybrid levels `hyam·P0 + hybm·ps`:
   - T, U and V are interpolated linearly in ln p.
   - Below the ERA5 surface, T follows the same lapse rate as the ps extrapolation, and U and V are held constant.
   - qv, qc, qi and ozone are remapped with a mass-conserving piecewise-linear method whose slopes are limited. This conserves column mass between the ERA5 surface and the model top, and creates no new extremes.
5. **State adjustment**:
   - Supersaturation with respect to liquid is removed, using EAMxx's Murphy–Koop formula. Supersaturation over ice is allowed up to liquid saturation, as in P3.
   - qv has a floor of 1e-12.
   - Ozone is converted from mass to volume mixing ratio.
   - ERA5 snow (`cswc`) is added to cloud ice by default, because P3's single ice category includes snow. ERA5 rain is not written, because EAMxx forces `qr` to 0 at start-up.

The output holds `T_mid`, `U`, `V`, `qv`, `qc`, `qi`, `o3_volume_mix_ratio`,
`ps` and `phis` (= `PHIS_d`), plus the hybrid coefficients, lat/lon and date.
It is CDF5, with columns in the topography file's `ncol_d` order. Each output
file records its inputs, method and tool revision in its global attributes.

## Usage

```bash
# 1. ERA5 model levels from CDS (needs ~/.cdsapirc and cdsapi)
python request_era5_ml.py submit      # later: status / download
# 2. convert GRIB to netCDF and extract the L137 a/b coefficients
#    (grib_to_nc.sh: to be added once the first CDS files arrive)
# 3. make the IC (init + parallel run + check) on Perlmutter
GRID=1024x2 sbatch run_make_ic.sh
```

Or step by step:

```bash
python make_ic.py init  --out IC.nc --source ml --era5-atm ... --era5-sfc ... --era5-ab ... \
                        --topo TOPO.nc --vert VERT.nc --date 2011-05-19 --hour 18
srun -N 8 --ntasks-per-node=1 -c 256 python make_ic.py run --out IC.nc
python make_ic.py check --out IC.nc --era5-pl-atm ERA5.atm.nc
```

`check` verifies the following on sampled columns:
- every chunk was written
- values are finite and within range
- moisture and ozone are non-negative
- there is no supersaturation
- `phis` matches the topography file
- hydrostatic consistency: 500 hPa height recomputed from ps, T, qv and `PHIS_d` against ERA5's analysed z500

## Status

- Tested end to end with ERA5 pressure-level input on the 128x2 grid. The
  1.15M-column IC took 21 s on one Perlmutter node and passed `check`.
- Model-level input is written but not yet run: the CDS request is pending, and
  the GRIB conversion script will be added when the files arrive.
- Defaults in `run_make_ic.sh` and `request_era5_ml.py` (work directories,
  account, topography paths) are for the CONUS 2026 INCITE runs on Perlmutter.
  Override them through the environment.

## Tests

```bash
python tests/test_kernels.py
```

The tests compare against analytic answers:
- interpolation reproduces linear and quadratic fields exactly
- the limiter creates no new extremes
- cross-polar solid-body rotation is reproduced
- remapping conserves mass and stays within bounds
- surface-pressure adjustment matches the isothermal case
- supersaturation is removed
- the parallel CDF5 writer round-trips data correctly
