"""Read old authored carrier/colour provenance; no app/project operations."""
from pathlib import Path
import hashlib,json,re
import numpy as np
R=Path(__file__).resolve().parent
P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game/Assets/EUnityValidation01')
B=R.parent/'eye-candidate49'
cells=json.loads((B/'fixtures/template43.json').read_text())['cells']
def texture(path):
    s=path.read_text();w=int(re.search(r'm_Width: (\d+)',s).group(1));h=int(re.search(r'm_Height: (\d+)',s).group(1))
    raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',s).group(1));return np.frombuffer(raw,np.uint8).reshape(h,w,4),w,h
rgba,_,_=texture(P/'SocketTemplate216/Inputs/TemplateRGBA.asset')
rows=[]
for index,eye in[(0,2),(1,1)]:
    for family,role in[('IrisPupil',1),('White',4)]:
        stem=f'Eye{index}_{family}';palette=P/f'EyeAuthoredSurface205/Palettes/{stem}.asset';mesh=P/f'EyeAuthoredSurface205/Meshes/{stem}.asset'
        a,w,h=texture(palette);colours={tuple(map(int,c))for c in a.reshape(-1,4)if c[3]>0}
        reference={tuple(c['rgba8'])for c in cells if c['eye']==eye and c['role']==role}
        s=mesh.read_text();vc=int(re.search(r'm_VertexCount: (\d+)',s).group(1));ic=int(re.search(r'indexCount: (\d+)',s).group(1));blend=bool(re.search(r'm_Shapes:\n\s+vertices: \[\]',s))
        assert reference<=colours,(eye,role,reference-colours)
        assert ic==3*(vc-1),'Expected old polygon fan, not individual cell quads'
        rows.append(dict(eye=eye,assignedRole=role,palette=str(palette),paletteSHA256=hashlib.sha256(palette.read_bytes()).hexdigest(),
            paletteDimensions=[w,h],rgba8=sorted(map(list,colours)),templateColoursWithinAssignedPalette=True,
            paletteSetExactlyEqualsTemplate=reference==colours,unusedPaletteColours=sorted(map(list,colours-reference)),
            mesh=str(mesh),meshSHA256=hashlib.sha256(mesh.read_bytes()).hexdigest(),vertices=vc,triangles=ic//3,
            representation='contour polygon fan, nearest palette UV; not source pixel-cell quad identities',noMeshBlendshapes=blend))
shader=P/'EyeAuthoredSurface205/Shaders/Eye205Surface.shader';s=shader.read_text()
assert 'o.rgba=float4(c.rgb,1)'in s and '_LineRGBA'not in s
role_text=(P/'SocketTemplate216/Inputs/TemplateRole.asset').read_text();role_data=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',role_text).group(1)),'<f4').reshape(272,480,4)
out=dict(templateOpaquePixels=int((rgba[...,3]>0).sum()),templateOpaqueOutsideTwentyCells=int(((rgba[...,3]>0)&(role_data[...,0]==0)).sum()),
    templateHasOnlyAssignedIrisWhiteRole=set(np.unique(role_data[role_data[...,0]>0,0]).tolist())=={1.,4.},
    templateRoleZWAllZero=bool(np.all(role_data[role_data[...,0]>0,2:]==0)),carriers=rows,
    runtimeShaderColourRule='sample own semantic _MainTex -> RGB direct; no native eyeline sampler in this shader',
    shaderSHA256=hashlib.sha256(shader.read_bytes()).hexdigest(),
    colourProvenanceLimit='Exact match to assigned old authored palettes; not proof of the original palette authoring capture or native iris UV purity',
    nativeLidPixelKeyFormFound=False,newUnityCalls=0,newCommit=False)
assert out['templateOpaquePixels']==20
(R/'PALETTE_AND_CARRIER_PROVENANCE.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items()if k!='carriers'},ensure_ascii=False,indent=2))
