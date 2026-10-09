#!/usr/bin/env python3
"""Photon shielding database for the lecture dashboard.

Model: infinite planar slab (reflective lateral boundaries), normally incident
monoenergetic photons, vacuum on both faces. Tally: photons crossing the
downstream face per source photon (scattered + secondary photons included).
Uncollided transmission is NOT tallied; the dashboard uses exp(-mu x) with mu
computed here from the same OpenMC photon library.

Usage:  python run_openmc.py [--particles 50000] [--batches 20] [--electron ttb|led]
Needs OPENMC_CROSS_SECTIONS pointing to a neutron+photon library (e.g. ENDF/B-VIII.0).
Output: data.json, and the data block of dashboard.html (if next to this script) is replaced.
"""
import argparse, json, re, tempfile, datetime, pathlib, sys
import numpy as np, openmc, openmc.data

candidate_paths = [
    pathlib.Path(__file__).resolve().parent / 'endfb-viii.1-hdf5' / 'cross_sections.xml',
    pathlib.Path.home() / 'Documents' / 'cross_sections' / 'cross_sections.xml',
]
if not openmc.config.get('cross_sections'):
    for candidate in candidate_paths:
        if candidate.exists():
            openmc.config['cross_sections'] = str(candidate)
            break

openmc_exec = str(pathlib.Path(sys.executable).resolve().parent / 'openmc')
if not pathlib.Path(openmc_exec).exists():
    openmc_exec = 'openmc'

ENERGIES = [0.1, 0.3, 0.662, 1.25, 3.0]   # MeV
MFP = [0.5, 1, 2, 3, 4, 5, 6, 8]           # slab thickness in uncollided mean free paths
MATS = {                                   # density g/cm3, mass fractions
    'water': (1.0, {'H': .111894, 'O': .888106}),
    'concrete': (2.3, {'H': .01, 'C': .001, 'O': .529107, 'Na': .016, 'Mg': .002,
                       'Al': .033872, 'Si': .337021, 'K': .013, 'Ca': .044, 'Fe': .014}),
    'lead': (11.35, {'Pb': 1.0}),
}
_photon = {}

def make_mat(rho, comp):
    m = openmc.Material()
    m.set_density('g/cm3', rho)
    for el, w in comp.items():
        m.add_element(el, w, 'wo')
    return m

def mu_cm(m, E_MeV):
    """Total photon attenuation coefficient (1/cm), coherent+incoherent+photoelectric+pair."""
    lib = openmc.data.DataLibrary.from_xml()
    dens = {}
    for nuc, v in m.get_nuclide_atom_densities().items():
        v = v[1] if isinstance(v, tuple) else v
        el = re.match('[A-Z][a-z]*', nuc).group()
        dens[el] = dens.get(el, 0.0) + v          # atoms / (barn cm)
    tot = 0.0
    for el, n in dens.items():
        if el not in _photon:
            _photon[el] = openmc.data.IncidentPhoton.from_hdf5(lib.get_by_material(el, data_type='photon')['path'])
        r = _photon[el].reactions
        mts = [502, 504, 522] + ([516] if 516 in r else [515, 517])
        tot += n * sum(float(r[mt].xs(E_MeV * 1e6)) for mt in mts)
    return tot

def run_case(m, E, x, particles, batches, electron):
    px = [openmc.XPlane(0, boundary_type='vacuum'), openmc.XPlane(x, boundary_type='vacuum')]
    py = [openmc.YPlane(-5, boundary_type='reflective'), openmc.YPlane(5, boundary_type='reflective')]
    pz = [openmc.ZPlane(-5, boundary_type='reflective'), openmc.ZPlane(5, boundary_type='reflective')]
    cell = openmc.Cell(fill=m, region=+px[0] & -px[1] & +py[0] & -py[1] & +pz[0] & -pz[1])
    st = openmc.Settings()
    st.run_mode, st.particles, st.batches = 'fixed source', particles, batches
    st.photon_transport, st.electron_treatment = True, electron
    Src = getattr(openmc, 'IndependentSource', None) or openmc.Source
    st.source = Src(space=openmc.stats.Point((1e-6, 0, 0)), angle=openmc.stats.Monodirectional((1, 0, 0)),
                    energy=openmc.stats.Discrete([E * 1e6], [1.0]), particle='photon')
    flt = [openmc.ParticleFilter(['photon']), openmc.SurfaceFilter([px[1]])]
    t1 = openmc.Tally(name='T'); t1.filters = flt; t1.scores = ['current']
    t2 = openmc.Tally(name='Es'); t2.scores = ['current']
    t2.filters = flt + [openmc.EnergyFilter(np.linspace(0, E * 1e6 * 1.001, 101))]
    model = openmc.Model(openmc.Geometry([cell]), openmc.Materials([m]), st, openmc.Tallies([t1, t2]))
    with tempfile.TemporaryDirectory() as d:
        sp = model.run(cwd=d, output=False, openmc_exec=openmc_exec)
        with openmc.StatePoint(sp) as s:
            a, b = s.get_tally(name='T'), s.get_tally(name='Es')
            T, sT = float(a.mean.ravel()[0]), float(a.std_dev.ravel()[0])
            mid = 0.5 * (b.filters[-1].bins[:, 0] + b.filters[-1].bins[:, 1])
            Et = float((b.mean.ravel() * mid).sum() / (E * 1e6))   # transmitted energy / source energy
    return T, sT, Et

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--particles', type=int, default=50000)
    ap.add_argument('--batches', type=int, default=20)
    ap.add_argument('--electron', default='ttb', choices=['ttb', 'led'])
    a = ap.parse_args()
    out = {'meta': {'source': 'openmc', 'version': openmc.__version__, 'electron': a.electron,
                    'histories': a.particles * a.batches, 'date': str(datetime.date.today())},
           'E': ENERGIES, 'materials': {}}
    for name, (rho, comp) in MATS.items():
        m = make_mat(rho, comp)
        out['materials'][name] = {'rho': rho, 'cases': {}}
        for E in ENERGIES:
            mu = mu_cm(m, E)
            c = {'mu': mu, 'x': [], 'T': [], 's': [], 'Et': []}
            for k in MFP:
                x = k / mu
                T, sT, Et = run_case(m, E, x, a.particles, a.batches, a.electron)
                for key, v in zip(['x', 'T', 's', 'Et'], [x, T, sT, Et]):
                    c[key].append(v)
                print(f'{name:9s} {E:6.3f} MeV  {k:3.1f} mfp  T={T:.3e} +/- {sT:.1e}', flush=True)
            out['materials'][name]['cases'][str(E)] = c
    js = json.dumps(out)
    pathlib.Path('data.json').write_text(js)
    html = pathlib.Path(__file__).with_name('dashboard.html')
    if html.exists():
        txt = html.read_text()
        txt = re.sub(r'(<script id="data" type="application/json">).*?(</script>)',
                     lambda mo: mo.group(1) + js + mo.group(2), txt, flags=re.S)
        html.write_text(txt)
        print('Embedded results in', html)
