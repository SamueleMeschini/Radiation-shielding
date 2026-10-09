# Shielding lab

An offline teaching dashboard for photon transmission through an effectively infinite planar slab. The original runner and page are preserved under `data/development/legacy_runner.py` and `legacy_dashboard.html`; the root files now point to the replacement. `data.json` and `data/development/legacy_400_histories.json` preserve the old 400-history data. Invalid pilot outputs are quarantined under `data/development/rejected_cases/`. The new dashboard never calls OpenMC at lecture time.

## Requirements and installation

Python 3.11+, NumPy, pytest for tests, and OpenMC 0.15.3 plus a compatible photon HDF5 library are required for simulation. Install the package with `python -m pip install -e .` in an OpenMC environment, and install the optional `test` extra if pytest is absent. Activate an environment with OpenMC, for example `conda activate openmc-env`, then run scripts from the project root. No web dependency or CDN is needed for the dashboard.

Cross-section libraries are intentionally excluded from this repository. Download or provide a compatible OpenMC library, then supply its manifest through `--cross-sections` or `OPENMC_CROSS_SECTIONS`. `check_environment.py` generates `data/library/cross_sections.xml` with relative paths to the locally available photon files. To simulate copper and tin, the local library must also contain matching neutron nuclide entries, as OpenMC requires them when loading the material.

```sh
LIB=/path/to/cross_sections.xml
python scripts/check_environment.py --cross-sections "$LIB"
python scripts/run_matrix.py --profile smoke --cross-sections "$LIB"
python scripts/run_matrix.py --profile development --cross-sections "$LIB" --workers 2 --stacks
python scripts/postprocess_results.py --cross-sections "$LIB" --cases data/development/cases --output dashboard/data.json
python scripts/build_dashboard.py --dataset dashboard/data.json --output dist/shielding_dashboard.html
python -m pytest -q tests  # after installing the test extra
osascript -l JavaScript scripts/dashboard_smoke.jxa.js  # optional macOS structural smoke test
```

For development, serve `dashboard/` with `python -m http.server 8000 --directory dashboard` and visit `http://localhost:8000`. The built `dist/shielding_dashboard.html` opens directly without a server or network.

## Resume and lecture run

Case JSONs are cached by specification and library manifest identifier. Re-run the same command after interruption; completed cases are reused. Each case has a separate working directory and log/statepoint files in `data/{development,lecture}/cases/work/`. `--workers 2` uses separate Python processes. `--limit N` limits a test run to the first N cases. Failed cases retain an error JSON; rerunning retries them.

```sh
python scripts/run_matrix.py --profile lecture --cross-sections "$LIB" --workers 2 --stacks
python scripts/postprocess_results.py --quality lecture --cases data/lecture/cases --cross-sections "$LIB" --output data/lecture/dashboard.json
python scripts/build_dashboard.py --dataset data/lecture/dashboard.json --output dist/shielding_dashboard.html
python scripts/validation_report.py data/lecture/dashboard.json
```

Lecture mode starts at 200,000 histories per case and adds independent rounds up to 2 million histories if a transmission target is unmet. Targets are 2% relative uncertainty for Tₙ ≥ 0.01 and 5% for 0.001 ≤ Tₙ < 0.01. Cases outside those ranges or missing the target are flagged. The current development profile uses 20,000 histories per case and is always marked development. `--quality lecture` requires the complete 486-case slab grid, curated stacks, one LED comparison, and at least 200,000 histories per case; cases below uncertainty targets remain visibly flagged. A full 486-case slab grid plus selected stacks can require hours to days and multiple GB of retained statepoints; wall time depends on hardware and energy. The small development matrix is much faster.

## Model and data limitations

The source is uniform over a 10 cm × 10 cm transverse cell, normally incident, with reflective sides and vacuum faces. Current at the downstream +x vacuum plane is outward and positive. Photon transport and atomic relaxation are enabled; TTB is the main electron treatment. OpenMC does not transport charged particles in general condensed-history fashion. Source results are per emitted photon. No dose quantities are computed.

The dashboard uses exact analytical zero-thickness anchors and log-linear scalar interpolation only within simulated thickness ranges. Energies are discrete. Spectra are shown only at direct simulated points; bins do not prove interaction histories. The charged-particle lab uses locally saved NIST ESTAR/ASTAR tables, with numerical integration anchored at the first tabulated CSDA range. ASTAR concrete is unavailable in the selected NIST materials. The stack controls select explicitly simulated configurations; changing to an unrun configuration shows no invented spectrum.

For physics details see `docs/physics_model.md`; for source and composition references see `docs/data_provenance.md`; for a guided class sequence see `docs/teaching_notes.md`. To debug a failed case, inspect its JSON `error` and its corresponding `work/<case_id>/round_*/` directory. If OpenMC cannot be imported, use the OpenMC environment. If photon files are missing, point to a complete local library. If a result is unavailable in the dashboard, run the corresponding case rather than extrapolating.
