from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
for value in [0,1,4]:
    mode='Cold'+str(value)+'97';OUT=HERE/('cold'+str(value));OUT.mkdir(exist_ok=False)
    s=(HERE/'RunFrozen96.cs').read_text().replace('ROOT96',str(HERE)).replace('OUTPUT96','cold'+str(value)+'/gpu-output').replace('REPORT96.json','cold'+str(value)+'/REPORT96.json').replace('COMPLETE96.marker','cold'+str(value)+'/COMPLETE96.marker').replace('DIRECT96','false').replace('DIRECT_DESCRIPTION96','fresh scope at partial Close50; policy'+str(value))
    s=s.replace('Directory.GetFiles(Path.Combine(Root,"fixtures"),"frame*.bin")','Directory.GetFiles(Path.Combine(Root,"fixtures"),"frame102.bin")').replace('rows.Count==7','rows.Count==1').replace('var cmd=new CommandBuffer{name="96 isolated actual source BVH and selector"};','FrozenComposition96 composition=null;var cmd=new CommandBuffer{name="96 isolated actual source BVH and selector"};').replace('engine.Dispatch(cmd,view,projection,false);Graphics.ExecuteCommandBuffer(cmd);','composition=new FrozenComposition96(Path.Combine(Root,"fixtures/composition"+frame+".bin"));engine.Dispatch(cmd,view,projection,false,'+str(value)+');engine.Compose(cmd,composition.Bindings);Graphics.ExecuteCommandBuffer(cmd);composition.Write(output,frame);').replace('finally{cmd.Release();}','finally{composition?.Dispose();cmd.Release();}')
    (OUT/(mode+'.cs')).write_text(s,encoding='utf-8')
    bundle([ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'eye-observer73/CreateOnly73.cs',HERE/'WholeEye96.cs',HERE/'FrozenComposition96.cs',HERE/'LiveSurface96.cs',OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
    relay=(ROOT/'final-eye95/capture-scale-correct/relay95.py').read_text().replace("'Verify95B')","'Verify95B','"+mode+"')")
    (OUT/'relay97.py').write_text(relay,encoding='utf-8')
print('Prepared three explicit cold tie policies. Default0 retains original and marks unknown; policies1/4 are unapproved art comparisons only.')
