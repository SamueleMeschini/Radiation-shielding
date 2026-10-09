"""Physics equations and safe interpolation, with MeV and cm conventions."""
import math

def attenuation(mu, x): return math.exp(-mu*x)
def mass_thickness(rho, x): return rho*x
def optical_thickness(mu, x): return mu*x
def hvl(mu): return math.log(2)/mu
def tvl(mu): return math.log(10)/mu
def stack_uncollided(layers): return math.exp(-sum(mu*x for mu,x in layers))
def compton(E, theta_deg):
    ep=E/(1+E/0.51099895*(1-math.cos(math.radians(theta_deg))))
    return {'photon_MeV':ep,'electron_MeV':E-ep,'electron_max_MeV':2*E*E/(0.51099895+2*E),'backscatter_MeV':E/(1+2*E/0.51099895)}
def log_interpolate(x, a, b):
    """Endpoints (x, value, sigma); rejects extrapolation and unresolved values."""
    x0,y0,s0=a; x1,y1,s1=b
    if not x0 <= x <= x1 or x0 == x1: raise ValueError('outside bracket')
    if y0 <= 0 or y1 <= 0: raise ValueError('unresolved endpoint')
    t=(x-x0)/(x1-x0)
    y=math.exp((1-t)*math.log(y0)+t*math.log(y1))
    return y, y*math.hypot((1-t)*s0/y0,t*s1/y1)
def superpose(lines, results):
    """lines: (energy MeV, photon weight), results: energy -> (T_N,s_N,T_E,s_E)."""
    if abs(sum(w for _,w in lines)-1)>1e-9: raise ValueError('weights must sum to one')
    if any(w<0 for _,w in lines): raise ValueError('negative weight')
    den=sum(E*w for E,w in lines)
    tn=sum(w*results[E][0] for E,w in lines)
    sn=math.sqrt(sum((w*results[E][1])**2 for E,w in lines))
    te=sum(E*w*results[E][2] for E,w in lines)/den
    se=math.sqrt(sum((E*w*results[E][3])**2 for E,w in lines))/den
    return {'T_N':tn,'sigma_N':sn,'T_E':te,'sigma_E':se,'mean_energy_MeV':den*te/tn if tn>0 else None}
def spectrum_moments(edges, values, sigmas, source_E):
    if len(edges)!=len(values)+1 or len(values)!=len(sigmas): raise ValueError('spectrum dimensions')
    mids=[(a+b)/2 for a,b in zip(edges,edges[1:])]
    return sum(values),sum(v*m for v,m in zip(values,mids))/source_E,math.sqrt(sum(s*s for s in sigmas))
