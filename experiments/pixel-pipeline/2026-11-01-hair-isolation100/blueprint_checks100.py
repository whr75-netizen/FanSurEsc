"""Small deterministic checks of supplied2.1 draft; no renderer changes."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
def components(points):
 p=set(points);n=0
 while p:
  n+=1;todo=[p.pop()]
  while todo:
   x,y=todo.pop()
   for q in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if q in p:p.remove(q);todo.append(q)
 return n
def thin(p):
 # IsInterior is assumed true; endpoints are not the selected centre.
 return {q for q in p if not((q[0]+1,q[1])in p and(q[0],q[1]+1)in p and(q[0]-1,q[1]-1)not in p)}
def main():
 p={(0,0),(1,0),(0,1)};q=thin(p);rot=lambda p:{(-y,x)for x,y in p}
 assert components(p)==1 and components(q)==2 and thin(rot(p))!=rot(q)
 K=3;generated=list(range(K));selected=[round(q*(K-1))+1 for q in [0,.5,1]];assert selected==[1,2,3]and selected[-1]not in generated
 result={'documents':[{'path':str(p),'SHA256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in [Path(r'C:\Users\15352\Desktop\Argon2.md'),Path(r'C:\Users\15352\Desktop\Argon2.1.md')]],'readOnlyDocuments':True,'declaredPaletteKIncludesOutline':K,'formulaGeneratedIndices':generated,'exampleHLSLShadeIndices':selected,'paletteContractMustChoose':'either K total includes outline and shades1..K-1, or separate shadeCount and totalCount; current example generator and lookup differ','Lcorner':{'source':sorted(p),'afterProposedRule':sorted(q),'components4Before':components(p),'components4After':components(q),'rotationCovariant':False,'qualification':'IsInterior definition absent in supplied draft; unconditional proposed local predicate does not protect topology'},'unimplementedBlueprintFunctions':['ResolvePaletteRegionId','IsTopContourCell','CleanupOrphanPixelsKernel'],'otherUnverifiedAssumptions':['sphere-biased sclera skin proxy fully closes all views/Close states','screen p previous-label hysteresis transports same feature identity','one material/UV group is one meaningful colour region','hair coverage0.5 is sufficient for temporal/curve quality'],'implementedInProduct':False}
 (HERE/'BLUEPRINT_CHECKS100.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Draft slot-index mismatch and direction/topology counterexamples verified; no Unity calls')
if __name__=='__main__':main()
