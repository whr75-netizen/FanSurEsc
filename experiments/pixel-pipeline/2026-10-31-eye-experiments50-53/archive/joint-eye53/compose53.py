"""Honest partial composition when frozen clean eye underlay is unavailable."""
import numpy as np
from PIL import ImageDraw
UNKNOWN=(250,0,200,255)

def old_eye_mask(d,eye):
    v=d['eye-visible'];mask=(np.rint(v[...,1])==eye)&(v[...,0]>0)
    # Never clear a selected external hair/brow/body pixel merely because a
    # pre-final diagnostic still contains an eye feature there.
    for key in['hair-meta','brow-meta']:
        a=d[key];mask&=~((a[...,0]>0)&(a[...,1]>.5)&(a[...,3]>1e-6))
    a=d['raw-meta'];mask&=~((a[...,0]>0)&(np.rint(a[...,1])>=8)&(np.rint(a[...,1])<=11))
    return mask

def partial_context(base,m,d,rows,visibility,destination_veto,eye=1):
    """Remove old eye evidence, mark unavailable underlay, then direct-fill P.

    Magenta is UNKNOWN diagnostic, not a chosen palette or fabricated skin.
    This output must not be labelled a complete faithful final-face render.
    """
    im=base.copy();draw=ImageDraw.Draw(im);old=old_eye_mask(d,eye)
    unknown={(int(x+m['x']),int(y+m['y']))for y,x in np.argwhere(old)}
    for x,y in unknown:
        xx,yy=(x-m['x'])*2,(y-m['y'])*2;draw.rectangle((xx,yy,xx+1,yy+1),fill=UNKNOWN)
    emitted=[]
    for r in rows:
        if not visibility[r['id']]or destination_veto(r):continue
        x,y=(r['xy'][0]-m['x'])*2,(r['xy'][1]-m['y'])*2
        draw.rectangle((x,y,x+1,y+1),fill=tuple(r['rgba8']));emitted.append(r);unknown.discard(tuple(r['xy']))
    return im,emitted,sorted(map(list,unknown))

def isolated_layer(size,m,rows):
    from PIL import Image
    im=Image.new('RGBA',size);draw=ImageDraw.Draw(im)
    for r in rows:
        x,y=(r['xy'][0]-m['x'])*2,(r['xy'][1]-m['y'])*2
        draw.rectangle((x,y,x+1,y+1),fill=tuple(r['rgba8']))
    return im
