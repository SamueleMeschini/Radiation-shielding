"""Macroscopic photon coefficients from the exact OpenMC photon library."""
from pathlib import Path
import hashlib
import re
import os
import xml.etree.ElementTree as ET
from .materials import make_openmc,ROOT
MTS={'coherent':(502,),'incoherent':(504,),'photoelectric':(522,),'pair_triplet':(515,517)}
_cache={}
def configure_library(path):
    """Add photon entries missing from an otherwise valid local manifest."""
    import openmc
    p=Path(path).resolve()
    if not p.is_file(): raise FileNotFoundError(p)
    tree=ET.parse(p);root=tree.getroot()
    out=ROOT/'data/library/cross_sections.xml';out.parent.mkdir(parents=True,exist_ok=True)
    have={x.get('materials') for x in root.findall('library') if x.get('type')=='photon'}
    for entry in root.findall('library'):
        entry.set('path',os.path.relpath((p.parent/entry.get('path')).resolve(),out.parent))
    photon_dir=p.parent/'photon'
    if photon_dir.is_dir():
        for file in sorted(photon_dir.glob('*.h5')):
            if file.stem not in have:
                ET.SubElement(root,'library',{'materials':file.stem,'path':os.path.relpath(file,out.parent),'type':'photon'})
    neutron_dir=ROOT/'data/library/neutron'
    have_neutron={x.get('materials') for x in root.findall('library') if x.get('type')=='neutron'}
    for file in sorted(neutron_dir.glob('ENDFB-8.1-NNDC_*.h5')):
        nuclide=file.stem.removeprefix('ENDFB-8.1-NNDC_')
        if nuclide not in have_neutron:
            ET.SubElement(root,'library',{'materials':nuclide,'path':os.path.relpath(file,out.parent),'type':'neutron'})
    # Read-only source manifest is preserved; generated paths are relative.
    temp=out.with_name(f'cross_sections_{os.getpid()}.tmp')
    tree.write(temp,encoding='utf-8',xml_declaration=True)
    os.replace(temp,out)
    openmc.config['cross_sections']=str(out.resolve())
    return p
def library_id(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
def coefficients(name,material,E):
    import openmc,openmc.data
    mat=make_openmc(name,material); lib=openmc.data.DataLibrary.from_xml()
    dens={}
    for nuc,v in mat.get_nuclide_atom_densities().items():
        n=v[1] if isinstance(v,tuple) else v
        el=re.match(r'[A-Z][a-z]*',nuc).group();dens[el]=dens.get(el,0)+n
    out={k:0.0 for k in MTS}
    for el,n in dens.items():
        if el not in _cache: _cache[el]=openmc.data.IncidentPhoton.from_hdf5(lib.get_by_material(el,data_type='photon')['path'])
        r=_cache[el].reactions
        missing={502,504,522}-set(r)
        if missing:raise ValueError(f'{el}: missing expected OpenMC 0.15.3 photon MTs {sorted(missing)}')
        for key,mts in MTS.items():
            for mt in mts:
                if mt in r: out[key]+=n*float(r[mt].xs(E*1e6))
    out['total']=sum(out.values());out['mass_total']=out['total']/material['density']
    if out['total']<=0: raise ValueError('nonpositive attenuation')
    return out

def absorption_edges(material):
    """K-shell binding energies in MeV, from the configured photon HDF5 files."""
    import openmc.data
    lib=openmc.data.DataLibrary.from_xml();out=[]
    for el in material['composition']:
        if el not in _cache:_cache[el]=openmc.data.IncidentPhoton.from_hdf5(lib.get_by_material(el,data_type='photon')['path'])
        relaxation=_cache[el].atomic_relaxation
        if relaxation and 'K' in relaxation.binding_energy:
            out.append({'element':el,'shell':'K','energy_MeV':float(relaxation.binding_energy['K'])/1e6})
    return sorted(out,key=lambda x:x['energy_MeV'])
