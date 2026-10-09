ObjC.import('Foundation');
function read(path){return $.NSString.stringWithContentsOfFileEncodingError(path,$.NSUTF8StringEncoding,null).js}
var nodes={};
function node(id){if(!nodes[id])nodes[id]={id:id,textContent:'',innerHTML:'',value:'',disabled:false,children:[],setAttribute:function(){},replaceChildren:function(){this.children=[]},append:function(){this.children.push(...arguments)},add:function(x){this.children.push(x);if(!this.value)this.value=x.value},querySelectorAll:function(){return []}};return nodes[id]}
var document={getElementById:node,createElementNS:function(){return node('svg-'+Math.random())}};
function Option(label,value){return {label:label,value:value}}
node('embedded-data').textContent=read('dashboard/data.json');node('particle').value='electron';node('particle-energy').value='1';node('angle').value='90';node('compare-value').value='1';node('target').value='0.5';
eval(read('dashboard/app.js')+'; this.__sample=sample;this.__state=state;this.__draw=drawExplore;');
if(!node('quality').textContent.includes('Development dataset'))throw Error('quality banner did not render: '+node('quality').textContent);
if(!node('metrics').innerHTML.includes('Photon transmission'))throw Error('explore metrics missing');
if(!node('compare-table').innerHTML.includes('Lead'))throw Error('comparison table missing');
if(!node('charged-table').innerHTML.includes('Mass CSDA range'))throw Error('charged data table missing');
if(!node('charged-output').textContent.includes('0.436'))throw Error('ESTAR water range did not integrate');
__state.energy=0.1;__state.source='mono';__state.material='water';__state.basis='mfp';__state.x=.25;__draw();if(!node('status').textContent.includes('OpenMC result'))throw Error('simulated point selection failed');
__state.x=0;__draw();if(!node('metrics').innerHTML.includes('1.000'))throw Error('exact zero anchor missing');
if(__sample('water',0.1,0).tn!==1||__sample('water',0.1,0).te!==1)throw Error('zero anchor failed');
if(__sample('water',0.1,1e9)!==null)throw Error('extrapolation accepted');
var low=JSON.parse(node('embedded-data').textContent).cases.find(c=>c.spec.kind==='slab'&&c.spec.material==='water'&&c.energy_MeV===0.1&&c.spec.optical_thickness===6);if(!low||low.quality!=='below_target')throw Error('low quality case not flagged');
node('material').onchange({target:{value:'lead'}});
if(!node('status').textContent.includes('lead')&&!node('metrics').innerHTML.includes('Photon transmission'))throw Error('material control failed');
node('source').onchange({target:{value:'co60'}});node('thickness').oninput({target:{value:1}});
if(!node('status').textContent.includes('Combined'))throw Error('source control failed');
node('source').onchange({target:{value:'mono'}});node('energy').onchange({target:{value:'3'}});if(!node('metrics').innerHTML.includes('Photon transmission'))throw Error('3 MeV control failed');
node('basis').onchange({target:{value:'mass'}});
if(!node('thickness-label').textContent.includes('g/cm'))throw Error('basis control failed');
'Offline dashboard structural controls passed';
