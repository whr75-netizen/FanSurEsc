from pathlib import Path
import json,struct
ROOT=Path(__file__).parent
review=json.loads((ROOT/'REVIEW572.json').read_text())
checked=0;nonopen=0;keep=0;fill=0;rows=[]
for record in review:
    frame=record['frame'];data=(ROOT/f'Stored572/{frame:03}_RESOLVED.bin').read_bytes();pos=0
    def get(fmt):
        global pos
        q=struct.unpack_from('<'+fmt,data,pos);pos+=struct.calcsize('<'+fmt);return q[0]if len(q)==1 else q
    def text():
        global pos
        n=0;shift=0
        while True:
            q=get('B');n|=(q&127)<<shift
            if q<128:break
            shift+=7
        s=data[pos:pos+n].decode();pos+=n;return s
    assert get('2i')==(572,frame);count=get('i');lookup={c['branch']:c for c in record['canonicalOpenCapContracts']};open_count=0
    for _ in range(count):
        identity,scope,mode=text(),text(),text();invalid=get('i');cells=[get('i')for _ in range(get('i'))];ports=[(text(),*get('2i2q'))for _ in range(get('i'))]
        if invalid<0:
            assert scope=='NON_OPEN_EVENTS_NOT_VALIDATED';nonopen+=1;continue
        row=lookup[identity];assert scope=='OPEN_CAP_SOURCE_PORTS_ONLY'and invalid==0
        layout=(ROOT/f'Stored572/{frame:03}_LAYOUT.bin').read_bytes();_,_,x,y,w,h=struct.unpack_from('<6i',layout)
        expected_cells=sorted((yy-y)*w+xx-x for xx,yy in row['retainedNegativeCells']);assert sorted(cells)==expected_cells
        expected_ports=sorted((p['sourcePort']['side'],(p['from'][1]-y)*w+p['from'][0]-x,(p['to'][1]-y)*w+p['to'][0]-x,p['positiveLeftBoundary'],p['positiveRightBoundary'])for p in row['mappedPorts'])
        assert sorted(ports)==expected_ports
        assert bool(cells)==mode.startswith('KEEP_')
        checked+=1;open_count+=1;keep+=bool(cells);fill+=not cells
    assert pos==len(data)and open_count==len(lookup)
    assert not record['removedCells']and not record['holes4']
    rows.append({'frame':frame,'openContracts':open_count,'allDecisionRecords':count,'newPositiveCells':len(record['addedCells']),'removedPositiveCells':0,'closedNegativeComponents4':0})
out={'scope':'stored seven inputs only; open cap/mouth contract; not runtime integration or full hair validation','csharpPythonPortAndOwnerRecordsExact':checked,'selectedKEEP':keep,'selectedFILL':fill,'nonOpenDecisionsNotValidated':nonopen,'rows':rows,'forelock71_73Retained':all(r['forelock232_45']for r in review if r['frame']in[71,72,73]),'originalClosedSourceRingsUnchanged':all(r['oldSourceRingsUnchanged']for r in review),'newRuntimeFrames':0,'productAssetChanges':0}
assert checked==136 and nonopen==92
(ROOT/'OUTPUT_VERIFICATION572.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
