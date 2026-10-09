"""Infinite broad slab approximated with reflective transverse boundaries."""
import numpy as np

def spectrum_edges(E):
    # eV: fine logarithmic bins at characteristic X-ray energies, then linear continuum.
    low=np.geomspace(1e3,min(1e5,E*1e6*0.8),80)
    high=np.linspace(low[-1],E*1e6*1.01,121)
    return np.unique(np.r_[0,low,high,E*1e6,E*1e6*1.001])

def build(layers,E,particles,batches,seed,electron='ttb',mixed=None):
    import openmc
    if any(x<=0 for _,x in layers): raise ValueError('positive layers required')
    planes=[openmc.XPlane(0,boundary_type='vacuum')]
    for i,(_,width) in enumerate(layers): planes.append(openmc.XPlane(planes[-1].x0+width,boundary_type='vacuum' if i==len(layers)-1 else 'transmission'))
    # The same transverse cell is repeated by specular reflection; source is uniform.
    y0=openmc.YPlane(-5,boundary_type='reflective');y1=openmc.YPlane(5,boundary_type='reflective')
    z0=openmc.ZPlane(-5,boundary_type='reflective');z1=openmc.ZPlane(5,boundary_type='reflective')
    cells=[]
    for i,(mat,_) in enumerate(layers):
        cells.append(openmc.Cell(fill=mat,region=+planes[i]&-planes[i+1]&+y0&-y1&+z0&-z1))
    st=openmc.Settings();st.run_mode='fixed source';st.particles=particles;st.batches=batches
    st.photon_transport=True;st.electron_treatment=electron;st.seed=seed
    energy=openmc.stats.Discrete([e*1e6 for e,_ in mixed],[w for _,w in mixed]) if mixed else openmc.stats.Discrete([E*1e6],[1])
    st.source=openmc.IndependentSource(space=openmc.stats.Box((1e-6,-5+1e-6,-5+1e-6),(1e-6,5-1e-6,5-1e-6),only_fissionable=False),angle=openmc.stats.Monodirectional((1,0,0)),energy=energy,particle='photon')
    flt=[openmc.ParticleFilter(['photon']),openmc.SurfaceFilter([planes[-1]])]
    n=openmc.Tally(name='photon_number');n.filters=flt;n.scores=['current']
    ef=openmc.EnergyFunctionFilter([1,10e6],[1,10e6])
    e=openmc.Tally(name='photon_energy_eV');e.filters=flt+[ef];e.scores=['current']
    edges=spectrum_edges(max([v for v,_ in mixed]) if mixed else E)
    s=openmc.Tally(name='photon_spectrum');s.filters=flt+[openmc.EnergyFilter(edges)];s.scores=['current']
    return openmc.Model(openmc.Geometry(cells),openmc.Materials([m for m,_ in layers]),st,openmc.Tallies([n,e,s])),edges
