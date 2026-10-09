# Validation report

Dataset: **development**; schema 1; library ID `d82931c3f115c388`.
Stored cases: 222; principal slab cases: 217; quality flags: {'target_met': 161, 'below_target': 61}.
Relative photon-number uncertainty: min 0.11%, median 0.84%, max 12.65%.

| Check | Result | Evidence |
|---|---|---|
| Zero anchor | PASS | T_N = T_E = B_N = B_E = 1 by exact postprocessing anchor |
| Uncollided law | PASS | exp(-μx) |
| HVL / TVL | PASS | 0.5 and 0.1 |
| Layer-order invariant | PASS | analytical product |
| Current ≥ uncollided within 3σ | PASS | 0 / 217 violations |
| Energy current bounded within 5σ | PASS | 0 violations |
| Number-current spectrum integral | PASS | 0 current discrepancies |
| Mean-energy identity | PASS | 0 discrepancies |
| Spectrum mean-energy agreement | PASS | 0 / 217 midpoint integration discrepancies >2% or 0.002 |
| NIST XCOM comparison | PASS | water 0.1 MeV: -0.04%; water 1.0 MeV: -0.12%; lead 0.1 MeV: +0.01%; lead 1.0 MeV: -0.37% |
| Direct mixed-source agreement | PASS | number z = 0.62; energy z = 1.74 |
| Equal areal-density stack | PASS | graded 2.761000 versus Cu 2.761000 g/cm² |
| Measured layer-order effect | PASS | graded minus reversed number current: 7.67σ; spectra are direct tallies |
| Development/lecture separation | PASS | dataset quality = development |

The development data are not lecture-quality. Low-statistics cases remain visible. The complete lecture grid has 486 positive-thickness slab cases plus four curated stacks and one LED comparison case.

The current surface tally is signed; a positive +x crossing of the downstream +x vacuum plane is outward. The positive measured currents and current ≥ uncollided checks support this orientation.

NIST references: [water](https://pml.nist.gov/PhysRefData/XrayMassCoef/ComTab/water.html) and [lead](https://pml.nist.gov/PhysRefData/XrayMassCoef/ElemTab/z82.html).
