# Photon shielding laboratory

[**Open the dashboard**](https://samuelemeschini.github.io/Radiation-shielding/)

This interactive laboratory lets you explore how photon radiation changes as it passes through shielding materials. The dashboard uses precomputed OpenMC simulations, so you can investigate the results immediately in a browser without installing OpenMC or downloading cross-section libraries.

## What you can investigate

- **Explore a shield:** change the photon source, energy, material, and shield thickness. Compare transmitted photons, transmitted energy, buildup, and the spectrum.
- **Compare materials:** compare water, concrete, lead, copper, tin, and PMMA using the same physical thickness, areal density, or optical thickness.
- **Photon interactions:** see how coherent scattering, Compton scattering, photoelectric absorption, and pair production vary with energy.
- **Spectral hardening:** follow how a mixed spectrum becomes richer in higher-energy photons as the shield gets thicker.
- **Layered shield explorer:** compare arrangements such as Pb → Sn → Cu and Cu → Sn → Pb. Each layer shows its thickness and areal density, and the dashboard compares the measured transmissions and spectra.
- **Charged particles:** inspect local ESTAR/ASTAR range data and compare physical and mass stopping ranges.

Every plot has its own scale controls. “Automatic” chooses a logarithmic vertical scale when the plotted positive values span at least two orders of magnitude. Points outside the simulated range are not extrapolated.

## Reading the main quantities

The dashboard defines:

- \(T_N\): the number of photons crossing the downstream surface per emitted source photon.
- \(T_E\): transmitted photon energy divided by the energy emitted by the source.
- \(T_{\mathrm{unc}}\): the uncollided transmission predicted by \(e^{-\mu x}\).
- \(B_N\) and \(B_E\): photon and energy buildup relative to uncollided transmission.

Uncertainties are one standard deviation from the Monte Carlo tallies. A layered-shield comparison reports the difference in \(T_N\), its propagated uncertainty, and a z score. The z score is described as unresolved below 2, moderately resolved from 2 to 3, and clearly resolved at 3 or above.

## A few questions to try

1. At the same physical thickness, which material transmits the fewest photons?
2. Does the answer change when materials have the same areal density?
3. Why can reversing two layers change the complete spectrum even when the uncollided transmission is unchanged?
4. How does increasing photon energy change the dominant interaction?
5. Why does the transmitted spectrum become harder with shield thickness?

## Scope and limitations

The model represents normally incident photons crossing a uniform planar slab with reflective transverse boundaries and a vacuum downstream surface. The dashboard reports photon transport quantities; it does not calculate dose or provide a complete charged-particle transport model.

The controls select simulated cases and interpolate only between nearby simulated thicknesses. Spectra are shown at simulated points and remain tied to their original energy bins. Layered comparisons are limited to arrangements that were simulated in advance. Statistical precision is shown with each result, and low-precision or unavailable results are labelled.

## Use it locally

The standalone file can also be downloaded from [dist/shielding_dashboard.html](dist/shielding_dashboard.html) and opened directly. It contains the data, styles, JavaScript, KaTeX, and fonts needed by the dashboard.

To serve the development version locally:

~~~
python3 -m http.server 8000 --directory dashboard
~~~

Then open <http://localhost:8000>. The development source uses dashboard/data.json; the published Pages site uses the lecture dataset embedded in the standalone build.

