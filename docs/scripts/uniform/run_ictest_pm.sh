#!/bin/bash
# ==============================================================================
# EAMxx test runs on a uniform grid with three initial conditions for
# 2011-05-19 18Z (L128v4): HICCUP default (fv2se_flx map), HICCUP bilinear,
# and the new tool. Everything else is the out-of-the-box F2010-SCREAMv1
# configuration for the grid (default topography, which the ICs were made
# for; climatological SST, identical in all runs), so differences come from
# the IC alone.
#
# The first case is built; the others are clones sharing its executable.
#
# Usage (Perlmutter login node; CIME needs python >= 3.9: module load cray-python/3.11.7):
#   NE=30  bash run_ictest_pm.sh            # create, build, submit all three
#   NE=120 STOP_DAYS=3 bash run_ictest_pm.sh
#   ONLY=newtool NE=30 bash run_ictest_pm.sh   # just one IC (it is then the base)
#   ONLY=newtool-pl BASE=<caseroot of the built newtool case> NE=30 bash run_ictest_pm.sh
# ==============================================================================
set -euo pipefail
NE=${NE:-30}
stop_days=${STOP_DAYS:-3}
tag=${TAG:-20261113}
e3sm=${E3SM_ROOT:-${HOME}/codes/e3sm/branches/conus200-production}
work=/pscratch/sd/b/bhillma/conus200/ne30_ic
icdir=${work}/output
g=ne${NE}np4
res=ne${NE}pg2_ne${NE}pg2
compset=F2010-SCREAMv1
atmchange=${e3sm}/components/eamxx/scripts/atmchange

declare -A ic=(
    [newtool-pl]=${icdir}/eamxx_ic.era5-pl.2011-05-19.18.${g}.L128_for_E3SMv4_c20260820.bicubic.20261113.nc
    [newtool]=${icdir}/eamxx_ic.era5-ml.2011-05-19.18.${g}.L128_for_E3SMv4_c20260820.bicubic.20261113.nc
    [hiccup-fv2se]=${icdir}/HICCUP.atm_era5.2011-05-19.18.${g}.L128v4.fv2se.20261113.nc
    [hiccup-bilin]=${icdir}/HICCUP.atm_era5.2011-05-19.18.${g}.L128v4.bilinear.20261113.nc
)
order=(${ONLY:-newtool hiccup-fv2se hiccup-bilin newtool-pl})
case ${NE} in
    30)  wall=01:00:00 ;;
    120) wall=06:00:00 ;;
    *)   wall=02:00:00 ;;
esac
for k in "${order[@]}"; do [[ -f ${ic[$k]} ]] || { echo "missing IC: ${ic[$k]}"; exit 1; }; done

# Output streams (physics_pg2): hourly 2D, per-step ps and precipitation for
# the initial adjustment, and 6-hourly 3D state.
write_yamls() {
    local casename=$1
    cat > eamxx_ictest_2d_1h.yaml <<EOF
%YAML 1.2
---
filename_prefix: ${casename}.eamxx.h2d
averaging_type: instant
max_snapshots_per_file: 24
output_control:
  frequency: 1
  frequency_units: nhours
  skip_t0_output: 'false'
fields:
  physics_pg2:
    field_names:
      - ps
      - SeaLevelPressure
      - precip_total_surf_mass_flux
      - VapWaterPath
      - LiqWaterPath
      - IceWaterPath
      - T_2m
      - wind_speed_10m
      - surf_sens_flux
      - surf_evap
      - LW_flux_up_at_model_top
      - SW_flux_up_at_model_top
      - T_mid_at_850hPa
      - omega_at_500hPa
...
EOF
    cat > eamxx_ictest_step.yaml <<EOF
%YAML 1.2
---
filename_prefix: ${casename}.eamxx.hstep
averaging_type: instant
max_snapshots_per_file: 96
output_control:
  frequency: 1
  frequency_units: nsteps
  skip_t0_output: 'false'
fields:
  physics_pg2:
    field_names:
      - ps
      - precip_total_surf_mass_flux
...
EOF
    cat > eamxx_ictest_3d_6h.yaml <<EOF
%YAML 1.2
---
filename_prefix: ${casename}.eamxx.h3d
averaging_type: instant
max_snapshots_per_file: 4
output_control:
  frequency: 6
  frequency_units: nhours
  skip_t0_output: 'false'
fields:
  physics_pg2:
    field_names:
      - ps
      - T_mid
      - qv
      - qc
      - qi
      - U
      - V
      - omega
...
EOF
}

base=${BASE:-}   # BASE=<built caseroot> adds clones to an existing build
for k in "${order[@]}"; do
    casename=ictest.${res}.${compset}.${k}.${tag}
    caseroot=${work}/cases/${casename}
    if [[ -d ${caseroot} ]]; then echo "exists: ${caseroot}"; exit 1; fi
    if [[ -z ${base} ]]; then
        ${e3sm}/cime/scripts/create_newcase --case ${caseroot} --compset ${compset} --res ${res} \
            --machine pm-gpu --compiler gnugpu --project e3sm_g --handle-preexisting-dirs r
        base=${caseroot}
    else
        ${e3sm}/cime/scripts/create_clone --case ${caseroot} --clone ${base} --keepexe
    fi
    cd ${caseroot}
    ./xmlchange RUN_STARTDATE=2011-05-19,START_TOD=64800
    ./xmlchange STOP_OPTION=ndays,STOP_N=${stop_days},REST_OPTION=never,DOUT_S=FALSE
    ./xmlchange JOB_WALLCLOCK_TIME=${wall} --subgroup case.run
    write_yamls ${casename}
    if [[ ${caseroot} == ${base} ]]; then
        ./case.setup
        ${atmchange} "initial_conditions::filename=${ic[$k]}"
        ${atmchange} "output_yaml_files=${caseroot}/eamxx_ictest_2d_1h.yaml,${caseroot}/eamxx_ictest_step.yaml,${caseroot}/eamxx_ictest_3d_6h.yaml"
        ./case.build
    else
        ./case.setup
        ${atmchange} "initial_conditions::filename=${ic[$k]}"
        ${atmchange} "output_yaml_files=${caseroot}/eamxx_ictest_2d_1h.yaml,${caseroot}/eamxx_ictest_step.yaml,${caseroot}/eamxx_ictest_3d_6h.yaml"
    fi
    ./preview_namelists > /dev/null
    ${e3sm}/components/eamxx/scripts/atmquery initial_conditions::filename
    ./case.submit
    echo "submitted ${casename}"
done
