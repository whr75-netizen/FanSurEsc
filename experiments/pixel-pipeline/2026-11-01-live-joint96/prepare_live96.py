from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'final-eye95'
def main():
    native=(OLD/'NativeRetarget95.cs').read_text().replace('NativeRetarget95','NativeRetarget96')
    native=native.replace(' RTHandle[][] wrappers;', ' public RTHandle[][] Handles96=>wrappers;\n public Vector2 Anchor96{get;private set;}public Vector4 Bounds96{get;private set;}\n RTHandle[][] wrappers;')
    native=native.replace('screenSign=-1;Bind(controlMaterial,','Anchor96=anchor;Bounds96=new Vector4(min.x,min.y,max.x,max.y);screenSign=-1;Bind(controlMaterial,')
    p=HERE/'NativeRetarget96.cs';assert not p.exists();p.write_text(native,encoding='utf-8')
    graph=(OLD/'GraphSources95.cs').read_text().replace('GraphSources95','GraphSources96').replace('NativeRetarget95','NativeRetarget96')
    graph=graph.replace(' readonly NativeRetarget96 retarget95;',' readonly LiveGraph96 joint96;readonly NativeRetarget96 retarget95;').replace('public GraphSources96(EyeFeature348 e,NativeRetarget96 nativeSource){','public GraphSources96(EyeFeature348 e,NativeRetarget96 nativeSource,LiveGraph96 joint){joint96=joint;').replace('retarget95.RecordGraph(graph,resources);','retarget95.RecordGraph(graph,resources);joint96.Record(graph);')
    p=HERE/'GraphSources96.cs';assert not p.exists();p.write_text(graph,encoding='utf-8')
    print('Prepared isolated Graph extension; no Unity import or execution.')
if __name__=='__main__':main()
