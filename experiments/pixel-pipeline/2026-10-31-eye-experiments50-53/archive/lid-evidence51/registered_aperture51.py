"""Restore the existing authored eye-over-face policy only in registered aperture.

This is a frozen-input trial, not a general skin/lid classifier. Native source
eyeline/hair/brow/body remain occluders. Unsupported sources/states are rejected.
"""
import copy
import numpy as np

def inside51(p,poly):
    x,y=p;flag=False
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)]
        if(a[1]>y)!=(b[1]>y)and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:flag=not flag
    return flag

def evaluate_registered51(cluster,key,state,m,d,bundle,registered_sources,representative,final_occlusion,projected_anchor):
    if m['sourceId']not in registered_sources or m['blinkWeight']!=0:raise ValueError('No registered source/state aperture')
    if m['styleJson']!=cluster.style_json:raise ValueError('Style changed')
    anchor,_=projected_anchor(m);rows,shift,_=cluster.place(key,state,anchor)
    for row in rows:
        eye=next(e for e in bundle['eyes']if e['eye']==row['eye'])
        q=np.array(row['referenceXY'])+[.75,.25]
        expected=(1 if inside51(q,eye['iris'])else 4)if inside51(q,eye['parent'])else 0
        if expected!=row['role']:raise ValueError('Pixel role is not bound to retained authored aperture')
        # Isolate the underlay rule to exactly this existing feature cell; never
        # zero the whole face input or treat carrier weights as a hard lid mask.
        x,y=row['xy'][0]-m['x'],row['xy'][1]-m['y']
        skin=d['S0META'].copy();region=skin[y*4:(y+1)*4,x*4:(x+1)*4]
        face=(np.rint(region[...,1])==4)&(np.rint(region[...,2])==row['eye'])
        region[face]=0
        local=dict(d);local['S0META']=skin
        rep=representative(local,m,row);row['representative']=rep
        blocks=final_occlusion(d,m,row['xy'],rep['depth'])if rep and rep.get('support')else['no-source-support']
        row['knownFinalBlocks']=blocks;row['visible']=bool(rep and rep.get('support')and not blocks)
        row['skinPolicy']='generic face underlay only inside registered existing-open aperture'
        row['nativeLidMaskInvented']=False
    return rows
