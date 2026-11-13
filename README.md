# EAMxx initial conditions from reanalyses

`make_ic.py` makes an EAMxx initial condition (IC) on an np4 (GLL) grid,
including regionally refined grids, directly from ERA5, the ECMWF operational
IFS analysis or MERRA-2. It does this in one pass, in parallel over columns. It replaces HICCUP for this purpose and does
not try to reproduce HICCUP's output.

## Why

HICCUP, as used for the CONUS x2/x3/x4 ICs, works like this:
- It interpolates horizontally on ERA5 pressure levels using a precomputed map
  file. The conservative maps gave blocky grid imprinting at km scales.
- It works on files one variable at a time, rewriting every file at every step.
  At x4 that meant more than a day on one node, more than 650 GB of temporary
  files and about 300 GB of memory, with no way to restart.

This tool instead:
- Reads the source on its native **model levels** (pressure levels are
  supported as a fallback).
- Interpolates horizontally **along model levels** with weights computed
  directly from the regular lat-lon grid, so no map file is needed.
- Does all the column physics in memory and writes each column range straight
  into one output file.
- Restarts: finished chunks are skipped on a rerun.

## Sources

| `--source` | Data | Levels | Grid | How to get it |
|---|---|---|---|---|
| `era5-ml` | ERA5 analysis | 137 hybrid | 0.25° | `request_era5_ml.py` (CDS, `~/.cdsapirc`), then `grib_to_nc.sh` |
| `ifs-ml` | ECMWF operational IFS analysis | 91 (before 2013-06-25) or 137 | 0.125° (T1279) or 0.1° (TCo1279, from 2016-03-08) | `request_ifs_ml.py` (MARS, `~/.ecmwfapirc`, needs MARS access), then `grib_to_nc.sh` |
| `merra2-ml` | MERRA-2 `inst3_3d_asm_Nv` | 72 hybrid | 0.5°×0.625° | `download_merra2_nv.sh` (NASA Earthdata login in `~/.netrc`) |
| `era5-pl` | ERA5 on pressure levels | 37 | 0.25° | CDS |
| `merra2-pl` | MERRA-2 `inst3_3d_asm_Np` | 42 | 0.5°×0.625° | on Perlmutter: `/global/cfs/projectdirs/m3522/cmip6/MERRA2` |

Use model levels when you can. With pressure-level input, levels that are underground
at neighbouring source points leak into the horizontal interpolation near steep terrain:
- ERA5 fills those levels with values ECMWF extrapolated.
- MERRA-2 marks them missing, and the tool fills them (T by the standard lapse rate, other fields constant).

Either way the source column is already 25–90 m off its own analysed 500 hPa height
over the Himalayas, Andes and Antarctica, before any adjustment.

How each source is read:
- **Hybrid coefficients:** for ERA5 and IFS they come from the GRIB `pv` array. For MERRA-2
  they are fitted from `DELP`, `PS` and `PL`, and the fit is checked to be exact.
- **Snow** (ERA5/IFS `cswc`) is added to cloud ice. MERRA-2 has no snow field.
- **Grid:** any regular global lat-lon grid works, in either latitude order and from any longitude origin.

## Method

1. **Horizontal**, from the source grid to each GLL node:
   - **Default**: bicubic (Keys/Catmull-Rom, smooth first derivatives) for T, ln ps and surface geopotential. Bilinear is an option.
   - **q, condensate and ozone**: the same interpolation, limited to the range of the surrounding 2×2 source points. This creates no new extremes and no negative values.
   - **Winds**: interpolated as 3D Cartesian vectors, then projected onto the local east and north directions. This is correct near and across the poles.
2. **Source column**: full-level pressures `a + b·ps` and half levels from the source's hybrid coefficients, or the pressure levels above the source surface. Geopotential is integrated upward from the source's surface geopotential using virtual temperature. EAMxx's constants are used throughout.
3. **Surface pressure on the model topography** (`PHIS_d` in the topography file, which EAMxx reads at run time):
   - Where the model surface is above the source surface, ln p is interpolated in geopotential within the source column. No lapse rate is assumed.
   - Where it is below, values are extrapolated with 6.5 K/km from the source surface virtual temperature, capped at 290.5 K as in Trenberth et al. (1993). The same profile gives T below the source surface, so ps and T are hydrostatically consistent.
4. **Vertical remap** to the target hybrid levels `hyam·P0 + hybm·ps`:
   - T, U and V are interpolated linearly in ln p.
   - Below the source surface, T follows the same lapse rate as the ps extrapolation, and U and V are held constant.
   - qv, qc, qi and ozone are remapped with a mass-conserving piecewise-linear method whose slopes are limited. This conserves column mass between the source surface and the model top, and creates no new extremes.
5. **State adjustment**:
   - Supersaturation with respect to liquid is removed, using EAMxx's Murphy–Koop formula. Supersaturation over ice is allowed up to liquid saturation, as in P3.
   - qv has a floor of 1e-12.
   - Ozone is converted from mass to volume mixing ratio.
   - Snow (ERA5/IFS `cswc`) is added to cloud ice by default, because P3's single ice category includes snow. Rain is not written, because EAMxx forces `qr` to 0 at start-up.

The output holds `T_mid`, `U`, `V`, `qv`, `qc`, `qi`, `o3_volume_mix_ratio`,
`ps` and `phis` (= `PHIS_d`), plus the hybrid coefficients, lat/lon and date.
It is CDF5, with columns in the topography file's `ncol_d` order. Each output
file records its inputs, method and tool revision in its global attributes.

## Requirements

- Python with numpy, numba and netCDF4. On Perlmutter, E3SM-Unified has all three:
  `source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh`
- ecCodes command-line tools, only for converting GRIB (`grib_to_nc.sh`).
- For downloads only: `cdsapi` (ERA5), `ecmwf-api-client` (IFS) or `wget` with a NASA Earthdata login (MERRA-2).

Inputs you supply:
- an EAMxx **topography file** with `lat_d`, `lon_d` and `PHIS_d` on the target np4 grid. It defines the target grid.
- a **vertical grid file** with `hyam`, `hybm`, `hyai`, `hybi` (and optionally `P0`), for example HICCUP's
  `files_vert/L128_for_E3SMv4_c20260820.nc` or `files_vert/L80_for_E3SMv3.nc`.
- the analysis date and hour.

## Usage

```bash
# ERA5 model levels: request from CDS, download (once the request completes), convert
python request_era5_ml.py submit   --dir $SRC --date 2011-05-19 --hour 18
python request_era5_ml.py download --dir $SRC
./grib_to_nc.sh $SRC/ERA5.ml.2011-05-19.18

# or the IFS operational analysis (MARS access required)
python request_ifs_ml.py --date 2011-05-19 --hour 18 --dir $SRC
./grib_to_nc.sh $SRC/IFS.ml.2011-05-19.18

# or MERRA-2 model levels
./download_merra2_nv.sh 2011-05-19 $SRC

# then, as a batch job
SOURCE=era5-ml DATE=2011-05-19 HOUR=18 SRC_DIR=$SRC TOPO=topo.nc VERT=L128.nc WORK=$OUTDIR \
    sbatch --account=XXX run_make_ic.sh
```

`run_make_ic.sh` documents its settings in its header. Its `#SBATCH` lines are for
Perlmutter CPU nodes; change them on the `sbatch` command line elsewhere.
`examples/conus2026_2011-05-19.sh` shows a complete setup (the CONUS 2026 INCITE RRM grids).

Or step by step:

```bash
python make_ic.py init  --out IC.nc --source era5-ml --atm 3d.nc --sfc sfc.nc --ab ab.txt \
                        --topo TOPO.nc --vert VERT.nc --date 2011-05-19 --hour 18
srun -N 8 --ntasks-per-node=1 -c 256 python make_ic.py run --out IC.nc
python make_ic.py check --out IC.nc --ref-pl ERA5.atm.nc     # MERRA-2: the Np file
```

`check` verifies the following on sampled columns:
- every chunk was written
- values are finite and within range
- moisture and ozone are non-negative
- there is no supersaturation
- `phis` matches the topography file
- hydrostatic consistency: 500 hPa height recomputed from ps, T, qv and `PHIS_d` against the source's analysed 500 hPa height (ERA5 `z`, MERRA-2 `H`), in columns with ps > 700 hPa

## Status

- Tested end to end on the 128x2 grid (1.15M columns) with pressure-level input.
  Each run took about 23 s on one Perlmutter node and passed `check`:

  | Source | z500 recomputed minus analysed |
  |---|---|
  | `era5-pl` | −0.3 ± 1.3 m |
  | `merra2-pl` | 0.6 ± 1.7 m |

- Model-level readers (`era5-ml`, `ifs-ml`, `merra2-ml`) are written and unit-tested
  but not yet run on real data:
  - `era5-ml`: the CDS request is pending.
  - `ifs-ml`: needs MARS access.
  - `merra2-ml`: needs an Earthdata login.
- The `pv` extraction in `grib_to_nc.sh` is tested on an ecCodes sample file.

## Tests

```bash
python tests/test_kernels.py                       # or: python -m pytest -q tests
VERT_FILE=L128.nc python tests/test_kernels.py     # use a real vertical grid instead of the synthetic one
```

The tests compare against analytic answers:
- interpolation reproduces linear and quadratic fields exactly
- the limiter creates no new extremes
- cross-polar solid-body rotation is reproduced
- remapping conserves mass and stays within bounds
- surface-pressure adjustment matches the isothermal case
- supersaturation is removed
- the parallel CDF5 writer round-trips data correctly
- a south-to-north source grid starting at -180° (MERRA-2's layout) interpolates exactly
- hybrid coefficients are recovered from level pressures, and non-hybrid levels are rejected
- missing values below ground are filled correctly
