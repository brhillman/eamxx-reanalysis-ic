# IC generation performance: eamxx-reanalysis-ic vs HICCUP

This compares how long it takes to make an EAMxx initial condition (IC) with HICCUP and with
eamxx-reanalysis-ic, and where each tool spends that time. The ICs are for the CONUS 2026
INCITE regionally refined grids (1024x2, 1024x3, 1024x4; np4, L128 E3SMv4 levels), from ERA5
at 2011-05-19 18Z, on Perlmutter CPU nodes (2 × 64-core AMD EPYC, 512 GB). For how the ICs
themselves differ, see [`comparison_with_hiccup.md`](comparison_with_hiccup.md).

## Summary

- **The new tool is 19–25× faster in wall time** (9 min against 2 h 43 min at x2, 19×; 29 min
  against 12 h 7 min at x4, 25×). It uses 8 nodes against HICCUP's 1, and it needs no separate map step.
- **HICCUP is dominated by I/O, not computation.**
  - At least 58–61 % of its time goes to three steps that only rewrite files.
  - Including state adjustments that are almost entirely I/O, the share is 65–68 %.
  - It writes about 9× the size of the final IC to disk: 2.4 TB for a 257 GB file at x2, and
    9.8 TB for a 1.1 TB file at x4.
- **The new tool writes each byte of the output about once.** Its computation takes 20–50 s per
  node.
- **The new tool is I/O-bound too.**
  - Writing takes 3–5× as long as computing in its column work.
  - Most of its total time is spent creating the output file. That is an inefficiency in the
    tool, not inherent work. Fixing it should take up to 5 min off x2 and up to 19 min off x4.

## Wall time and resources

| Grid (columns) | HICCUP bilinear: IC step | HICCUP: map step | eamxx-reanalysis-ic |
|---|---|---|---|
| 1024x2 (71.2M) | 2 h 43 min, 1 node, 207 GB peak | 14 min on 16 nodes | 8 min 47 s on 8 nodes, 50 GB peak per node |
| 1024x3 (117.2M) | 4 h 29 min, 1 node, 202 GB peak | 4.5 min on 16 nodes | 14 min 1 s on 8 nodes, 80 GB peak per node |
| 1024x4 (300.0M) | 12 h 7 min, 1 node, 413 GB peak | 10 min on 16 nodes | 28 min 45 s on 8 nodes, 139 GB peak per node |

| Node-hours | HICCUP (IC + map) | eamxx-reanalysis-ic |
|---|---|---|
| 1024x2 | 2.7 + 3.8 = 6.5 | 1.2 |
| 1024x3 | 4.5 + 1.2 = 5.7 | 1.9 |
| 1024x4 | 12.1 + 2.7 = 14.8 | 3.8 |

The new-tool runs are the current `20261113b` ICs; the HICCUP runs are the HICCUP `20261113`
bilinear ICs (HICCUP fc603d6, multifile workflow, ESMF bilinear map). Peak memory is sacct
MaxRSS. HICCUP's map is made once per grid and source grid; the node-hours above count it once.

## Where HICCUP's time goes

HICCUP's multifile workflow (needed for grids this large) keeps one temporary file per variable,
and most steps read each file, change it, and write it back. Times are from HICCUP's own step
timers. The state-adjustment total includes its three sub-steps, and the top-level steps add up
to the total.

| Step | What it does | x2 | x3 | x4 |
|---|---|---|---|---|
| `remap_horizontal_multifile` | `ncremap` with the precomputed map, one variable at a time | 1,237 s | 1,982 s | 6,051 s |
| `rename_vars_multifile` | loads every file and rewrites it to rename variables | 1,265 s | 2,241 s | 5,718 s |
| `add_time_date_variables_multifile` | loads every file and rewrites it to add time variables | 1,373 s | 2,307 s | 5,816 s |
| `surface_adjustment_multifile` | surface pressure on the model topography | 15 s | 18 s | 51 s |
| `remap_vertical_multifile` | vertical interpolation, file by file | 2,144 s | 3,095 s | 7,931 s |
| `atmos_state_adjustment_multifile` | supersaturation (243 s at x2), cloud water (228 s), ozone units (238 s; one multiplication) | 709 s | 1,244 s | 3,467 s |
| `combine_files` | merges the per-variable files into the IC | 3,022 s | 5,234 s | 14,564 s |
| **Total** | | **9,766 s (2.7 h)** | **16,124 s (4.5 h)** | **43,611 s (12.1 h)** |

Grouped by the kind of work:

| | x2 | x3 | x4 |
|---|---|---|---|
| File rewrites only (rename, add time, combine) | 58 % | 61 % | 60 % |
| State adjustments (trivial arithmetic on whole files) | 7 % | 8 % | 8 % |
| Remapping (computation plus its own I/O) | 35 % | 31 % | 32 % |
| Surface pressure | 0.2 % | 0.1 % | 0.1 % |

- **At least 58–61 % is pure I/O.** The three file-rewrite steps do no computation. Merging the
  files alone takes 50 min at x2 and 4 h at x4.
- **65–68 % counting the state adjustments.** These steps read and rewrite whole files for
  arithmetic that takes a negligible fraction of that time.
- **The remapping steps contain I/O as well**, but HICCUP's timers do not separate it. The true I/O
  share is therefore higher than 68 %.

Bytes moved, from Slurm's per-job filesystem counters:

| | x2 | x3 | x4 |
|---|---|---|---|
| Final IC size | 257 GB | 424 GB | 1,085 GB |
| HICCUP: read / written | 1.4 / 2.4 TB | 2.3 / 3.9 TB | 5.9 / 9.8 TB |
| HICCUP: written ÷ IC size | 9.1× | 9.1× | 9.1× |
| eamxx-reanalysis-ic: written | 248 GB | 448 GB | 1,217 GB |
| eamxx-reanalysis-ic: written ÷ IC size | 1.0× | 1.1× | 1.1× |

The HICCUP multipass design writes the whole IC about nine times. That is the main reason it takes
hours, and why it scales with the output size rather than with the computation.

## Where the new tool's time goes

The new tool runs in three phases: `init` creates the output file; `run` processes 1M-column
chunks in parallel (one task per node) and writes each chunk into the file at its final position;
`check` validates a sample of columns. Phase times are from job and step timestamps. Compute and
write times are summed from per-chunk log lines and divided by the 8 tasks.

| Phase | x2 | x3 | x4 |
|---|---|---|---|
| `init`: create the output file | 5 min 14 s | 8 min 32 s | 19 min 31 s |
| `run`: column work | 1 min 59 s | 3 min 7 s | 6 min 20 s |
| – of which compute, per node | 20 s | 31 s | 51 s |
| – of which writing, per node | 68 s | 107 s | 280 s |
| – of which start-up and reading the source | ~31 s | ~49 s | ~49 s |
| `check` | 1 min 33 s | 2 min 21 s | 2 min 53 s |
| **Total** | **8 min 47 s** | **14 min 1 s** | **28 min 45 s** |

- **Computation is a small part of the total:** 20–51 s per node, 3–4 % of the wall time.
- **Writing the chunks takes 3–5× as long as computing them.** Each node writes about 25 GB at x2
  and 127 GB at x4.
- **Creating the output file is the largest phase, and it should not be.**
  - A profile of `init` at x2 found 373 of its 463 s in the 21 variable definitions, about 18 s
    each. Another 87 s were spent in the rest of the function. The profile ran on a login node,
    which is slower than the 314 s `init` took in the job.
  - The job wrote 45 GB during this phase although data filling is off (190 GB at x4). Each
    definition appears to make netCDF rearrange the file as it grows.
  - Defining all variables in a single pass should remove most of this. If `init` drops to a few
    seconds, x2 would take about 4 min and x4 about 10 min. This has not been done or measured yet.

## Caveats

- **Different node counts.** HICCUP's IC step is serial Python on one node. Its map step uses
  16 nodes. The new tool uses 8 nodes, one task per node. Node-hours are the fairer comparison of
  cost; wall time is what a user waits for.
- **HICCUP bilinear is HICCUP at its best here.** It uses the latest code and a bilinear map; the
  default conservative-map workflow was not timed on these grids. The earlier HICCUP x4 IC
  (20260918) took more than a day, with more than 650 GB of temporary files.
- **One run each.** These are single runs on a shared filesystem (Perlmutter scratch), so I/O
  times vary from run to run. The fractions are more robust than the absolute times.
- **Restarts.** HICCUP cannot resume after a failure. The new tool skips finished chunks when it is
  rerun.

## Sources

| | x2 | x3 | x4 |
|---|---|---|---|
| HICCUP IC job (log) | 61196883 (`hiccup_1024x2_ic.61196883.out`) | 61196912 | 61178939 |
| HICCUP map job | 61196882 | 61196884 | 61178936 |
| eamxx-reanalysis-ic job | 61236355 | 61236356 | 61236357 |

HICCUP step times are from the timers HICCUP prints at the end of each log. Bytes moved and memory
are from `sacct` (`TRESUsageOutTot`, `MaxDiskRead`, `MaxDiskWrite`, `MaxRSS`). New-tool chunk
times are the `compute … s write … s` lines in its log. The `init` profile was
`python -m cProfile make_ic.py init …` on the 1024x2 grid.
