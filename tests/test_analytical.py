import math
import pytest
from shielding_dashboard.analytical import attenuation,hvl,tvl,stack_uncollided,log_interpolate,superpose,spectrum_moments,compton

def test_exact_anchor_and_hvl_tvl():
    mu=.17
    assert attenuation(mu,0)==1
    assert attenuation(mu,hvl(mu))==pytest.approx(.5)
    assert attenuation(mu,tvl(mu))==pytest.approx(.1)
    assert stack_uncollided([(mu,2),(.3,4)])==stack_uncollided([(.3,4),(mu,2)])

def test_interpolation_and_rejection():
    v,s=log_interpolate(1,(0,1,0),(2,.25,.025))
    assert v==pytest.approx(.5)
    assert s/v==pytest.approx(.05)
    with pytest.raises(ValueError):log_interpolate(3,(0,1,0),(2,.25,.025))
    with pytest.raises(ValueError):log_interpolate(1,(0,1,0),(2,0,.01))

def test_superposition():
    v=superpose([(.1,.5),(1,.5)],{.1:(.2,.01,.1,.005),1:(.8,.02,.7,.01)})
    assert v['T_N']==pytest.approx(.5)
    assert v['T_E']==pytest.approx((.1*.5*.1+1*.5*.7)/.55)
    assert v['mean_energy_MeV']==pytest.approx(.55*v['T_E']/.5)
    with pytest.raises(ValueError):superpose([(.1,.4)],{.1:(1,0,1,0)})

def test_spectrum_and_compton():
    n,e,s=spectrum_moments([0,1,2],[.3,.2],[.03,.02],2)
    assert n==pytest.approx(.5) and e==pytest.approx(.225)
    assert s==pytest.approx(math.hypot(.03,.02))
    a=compton(1,0);b=compton(1,180)
    assert a['photon_MeV']==1 and a['electron_MeV']==0
    assert b['photon_MeV']==pytest.approx(b['backscatter_MeV'])
