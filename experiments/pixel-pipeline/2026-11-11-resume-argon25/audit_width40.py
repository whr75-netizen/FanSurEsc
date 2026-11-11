"""Read-only source seam/width provenance audit; no renderer/GPU invocation."""
from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image
from surface_paths34 import native
from trace_contour40 import geometry,contour
H=Path(__file__).resolve().parent;G=H/'face40';C=G/'authored/capture';O=G/'analysis-authored'

def bilinear_green(image,uv):
    # Image stores PNG top-down; native() returns Unity V-flipped raw mesh UV.
    h,w=image.shape;xy=np.asarray(uv,float)*[w,h]-.5;ij=np.floor(xy).astype(int);f=xy-ij
    val=0.
    for dy in [0,1]:
        for dx in [0,1]:
            val+=image[(h-1-(ij[1]+dy)%h),((ij[0]+dx)%w)]*(f[0] if dx else 1-f[0])*(f[1] if dy else 1-f[1])
    return float(val/255)

def main():
    surface,binding=native();image=np.asarray(Image.open(G/'analysis-directed/SOURCE_WIDTH_MASK40.png').convert('RGBA'))[:,:,1];rows=[]
    for f in json.loads((C/'COMPLETE.json').read_text())['frames']:
        g=geometry(C/('geometry-frame'+str(f['frame'])+'.bin'));assert g['sourceId']==f['sourceId'];weld=g['points']['weld'];tri=g['indices'][3];assert np.array_equal(tri,surface.indices)
        edge={}
        for t in tri:
            for a,b in zip(t,np.roll(t,-1)):
                key=tuple(sorted([int(weld[a]),int(weld[b])]))
                if key[0]==key[1]:continue
                edge.setdefault(key,[]).append((int(a),int(b)))
        conflicts=[];different=[]
        for e in contour(g):
            incidences=edge[e['key']];assert len(incidences)==2
            for node in e['key']:
                vertices=[next(v for v in inc if int(weld[v])==node)for inc in incidences];uvs=surface.uv[vertices];samples=[bilinear_green(image,uv)for uv in uvs]
                if not np.array_equal(uvs[0],uvs[1]):different.append({'edgeID':e['id'],'weld':node,'sourceVertices':vertices,'sourceUV':uvs.tolist(),'idealGreen':samples})
                if (samples[0]>0)!=(samples[1]>0):conflicts.append({'edgeID':e['id'],'weld':node,'sourceVertices':vertices,'idealGreen':samples})
        rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'selectedSourceSegments':len(contour(g)),'differentIncidentUVEndpoints':len(different),'supportPolarityConflicts':conflicts,'differentUV':different})
    p=O/'WIDTH_PROVENANCE40.json';p.write_text(json.dumps({'binding':binding,'sourceWidthPNG_SHA256':hashlib.sha256((G/'analysis-directed/SOURCE_WIDTH_MASK40.png').read_bytes()).hexdigest(),'scope':'CPU ideal bilinear seam provenance only, not GPU sampler exactness or variable-thickness policy','rows':rows},indent=2),encoding='utf-8',newline='\n');print(json.dumps({'frames':len(rows),'differentUVEndpoints':[r['differentIncidentUVEndpoints']for r in rows],'supportPolarityConflicts':[len(r['supportPolarityConflicts'])for r in rows]}))
if __name__=='__main__':main()
