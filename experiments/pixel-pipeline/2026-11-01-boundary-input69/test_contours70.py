from pathlib import Path
import json,numpy as np
from source_contours70 import trace_evidence
from schema69 import shade_labels
R=Path(__file__).resolve().parent;cases=[]
def blank():return {'x':np.zeros((10,10),bool),'y':np.zeros((10,10),bool)}
a=blank();b=blank();a['x'][1:5,3]=True;b['x'][5:9,3]=True;g=trace_evidence({'persistent':a,'uncertain':b},'source-fixture');assert g['edges']==8 and len(g['paths'])==1 and g['paths'][0]['uncertain'] and len(g['paths'][0]['edgeTiers'])==8;cases.append('confidence transition keeps one connected curve with per-edge tiers')
rev=trace_evidence({'uncertain':b,'persistent':a},'source-fixture');assert g==rev;cases.append('tier/scan order does not change path identity')
strong=trace_evidence({'persistent':a,'fine':a},'overlap');assert all(not p['uncertain'] and not p['hardFeature'] for p in strong['paths']);cases.append('redundant fine evidence does not downgrade persistent confidence')
a=blank();a['x'][1:6,2]=True;a['y'][2,3:6]=True;g=trace_evidence({'uncertain':a},'T');assert len(g['paths'])==3 and len([p for p in g['pins'] if p['degree']==3])==1;assert all(p['pinnedStart'] and p['pinnedEnd'] for p in g['paths']);cases.append('T-junction and endpoints pin all three full branches')
a=blank();a['x'][1:9,2:4]=True;g=trace_evidence({'fine':a},'thin');assert len(g['paths'])==2 and all(p['edgeCount']==8 for p in g['paths']);cases.append('paired one-texel ribbon edges remain distinct, no size deletion')
a=blank();a['x'][1,1:3]=True;a['y'][0:2,2]=True;g=trace_evidence({'fine':a},'hole');assert len(g['paths'])==1 and g['paths'][0]['closed'] and g['edges']==4;cases.append('small closed boundary remains a loop')
a=blank();a['x'][1:4,2]=True;a['x'][5:9,2]=True;g=trace_evidence({'uncertain':a},'gap');assert len(g['paths'])==2 and g['newEdges']==0 and not g['gapClosing'];cases.append('missing source edge is not bridged into a new reference curve')
for n in [2,3,4]:
 p=np.zeros((1,n,4),np.float32);p[0,:,0]=np.arange(n)/(n-1);assert np.array_equal(shade_labels(p,np.ones((1,n),bool),'LegacySignals335.classifier_after_ShadeBoundary',n),np.arange(n)[None])
cases.append('producer-tagged2/3/4-step Q keeps intermediate IDs')
p=np.zeros((1,1,4),np.float32);p[0,0,0]=.5
try:shade_labels(p,np.ones((1,1),bool),'LegacySignals335.classifier_after_ShadeBoundary',4)
except ValueError:cases.append('nondeclared half-level rejected for4-step source')
else:raise AssertionError('wrong level accepted')
try:shade_labels(p,np.ones((1,1),bool),'EyeFeature348.postEyeUV',2)
except ValueError:cases.append('post-eye UV cannot become shade by numeric coincidence')
else:raise AssertionError('wrong schema accepted')
# This is an identifiability fixture for the class of continuous fields, NOT a
# claim that the real scene contains these oscillations. Sparse samples alone
# cannot certify which intermediate contour is the intended shape.
points=np.array([[.25,.25],[.25,.75],[.75,.25],[.75,.75],[.5,.5]])
f=lambda x,y:.45+.55*np.sin(4*np.pi*x)**2*np.sin(4*np.pi*y)**2
assert np.allclose(f(points[:,0],points[:,1]),.45,rtol=0,atol=1e-14)
t=(np.arange(512)+.5)/512;x,y=np.meshgrid(t,t);dense=f(x,y);fraction=float((dense>=.5).mean());assert fraction>.1
ambiguity={'meaning':'synthetic counterexample, not a render reproduction','measuredSamples':[{'xy':p.tolist(),'A':.45,'B':float(f(*p))} for p in points],'continuousFieldA':'constant.45','continuousFieldB':'.45+.55*sin(4*pi*x)^2*sin(4*pi*y)^2','denseBrightAreaA':0,'denseBrightAreaB':fraction,'inference':'continuity alone does not identify a unique between-sample contour; requires an explicit prior or independent observations'};(R/'REFERENCE_AMBIGUITY70.json').write_text(json.dumps(ambiguity,indent=2)+'\n',encoding='utf-8');cases.append('two continuous fields share native/centre samples but have different contours')
real=json.loads((R/'CURVE_REPORT70.json').read_text());graph=json.loads((R/'ORDERED_SOURCE70.json').read_text());assert not real['curveCorrectionApplied'] and all(not p['hardFeature'] and len(p['edgeTiers'])==p['edgeCount'] for s in graph['sources'] for p in s['graph']['paths']);cases.append('actual source confidence and whole paths retained without artistic promotion')
projection=np.load(R/'CURVE_PROJECTION70.npz');assert len(projection['curve'])==len(projection['placement'])==len(projection['face'])==len(projection['segments']);cases.append('actual repeated source curve placements retain separate geometry keys')
assert projection['sourceParameter'].shape==(len(projection['segments']),2) and np.all(projection['sourceParameter'][:,1]>projection['sourceParameter'][:,0]);cases.append('projected pieces keep ordered source parameters and do not bridge visibility gaps')
result={'passed':len(cases),'cases':cases,'UnityCalls':0,'limits':'graph representation/provenance tests; not aesthetic/analytic-curvature/temporal success'};(R/'CONTOUR_TEST70.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
