"""Evidence repackaging only: no new algorithm output or rendered RGB."""
import numpy as np,json
from PIL import Image,ImageDraw
from native109 import H,R,read,font,bilinear

def picture(mask,colour=(50,211,208)):
    image=np.full((*mask.shape,3),[30,43,57],np.uint8);image[mask]=colour;return Image.fromarray(image)
def main():
    cache=read(H/'NATIVE_CACHE109.json');domain=np.load(H/'NATIVE_DOMAIN109.npz');measure=read(H/'MEASURE109.json');history=read(H/'HISTORY109.json');related=R/'joint-model108'if(R/'joint-model108').exists()else R/'2026-11-01-joint-objective108';base=read(related/'RESULTS108.json');board=Image.new('RGB',(1280,1050),'#111923');dr=ImageDraw.Draw(board)
    dr.text((22,18),'109: real carrier mapping, area/line distortion, and intrinsic source-form evidence',font=font(20),fill='white');dr.text((22,54),'Diagnostic figures only. No new final eye RGB, palette, GPU dispatch or design size.',font=font(17),fill='#ffc376')
    d=max((d for row in measure['rows']if row['Close']==100 for d in row['destinations']if d['sameConnectedCarrier']),key=lambda d:abs(d['sourceDepthWouldBeWrongBy']))
    tex=Image.fromarray(domain['rgba']);crop=tex.crop((620,25,760,145));bg=Image.new('RGB',crop.size,'#1e2c3b');bg.paste(crop,mask=crop.getchannel('A'));scale=3;bg=bg.resize((bg.width*scale,bg.height*scale),Image.Resampling.NEAREST);board.paste(bg,(22,110));xy=[]
    for uv,col in [(d['sourceUV'],'#00ffe3'),(d['targetUV'],'#ffc25c')]:
        q=(np.array([uv[0]*1024,(1-uv[1])*256])-[620,25])*scale+[22,110];xy.append(tuple(q));dr.ellipse((q[0]-5,q[1]-5,q[0]+5,q[1]+5),outline=col,width=3)
    dr.line(xy,fill='#ffbf68',width=2)
    for i,text in enumerate(['105 same-packet frame104 / eye1 / cell (12,4)',f'source primitive {d["sourcePrimitive"]} -> target {d["targetPrimitive"]}',f'same carrier component / {d["carrierTriangleHops"]} triangle hops',f'continuous move {d["sourceToTargetCanonicalPixels"]:.4f}px',f'depth MUST change by {d["sourceDepthWouldBeWrongBy"]*1000:.3f}mm','target original alpha=0: source pigment transport required','full captured face geometry clear; external hair NOT verified']):dr.text((480,112+35*i),text,font=font(17),fill='#afcfdf'if i else'white')
    dr.text((22,485),'Closed105: source area error and one-cell line support are different criteria',font=font(20),fill='white')
    for j,owner in enumerate([1,2]):
        row=next(x for x in measure['rows']if x['Close']==100 and x['owner']==owner);geo=next(x for x in read(H/'GEOMETRY109.json')if x['frame']==104);curve=np.array(next(x for x in geo['eyes']if x['owner']==owner)['nativePigmentCurve']);q=base['closed105-frame104']['noCurve'][str(owner)];a=np.zeros((8,18),bool);b=a.copy()
        for(y,x),p in zip(q['points'],q['massFirst']['labels']):
            if p==3:a[y,x]=True
        for y,x in np.floor(curve[:,::-1]).astype(int):
            if 0<=y<8 and 0<=x<18:b[y,x]=True
        x=22+j*620;board.paste(picture(a,(219,132,79)).resize((270,120),Image.Resampling.NEAREST),(x,535));board.paste(picture(b).resize((270,120),Image.Resampling.NEAREST),(x+290,535));dr.text((x,660),f'eye{owner}: area {row["measuredVisibleAreaCells"]:.3f}; mass-first misses {row["areaPriorityCurveLoss"]["unrepresentedLengthFraction"]:.1%} of curve',font=font(15),fill='#cadbe7');dr.text((x,688),f'line diagnostic: {row["sourceCurveFloorPathCellsInsideROI"]} cells; area excess {row["oneCellPathAreaExcessOverMeasuredArea"]:.3f}',font=font(15),fill='#a3dce1')
    dr.text((22,748),'F105 exact108 mass/data tie: existing immutable source bank distinguishes the layouts',font=font(20),fill='white');f=next(x for x in read(H/'HISTORY_TIED_INPUTS109.json')if x['frame']==105)
    for j,c in enumerate(f['candidates']):
        a=np.zeros((8,18),int)
        for(y,x),p in zip(f['q']['points'],c):a[y,x]=p
        rgb=np.full((8,18,3),[30,43,57],np.uint8)
        for p,col in [(1,[135,85,234]),(2,[220,235,229]),(3,[223,105,83])]:rgb[a==p]=col
        board.paste(Image.fromarray(rgb).resize((324,144),Image.Resampling.NEAREST),(22+j*400,790))
        dr.text((22+j*400,940),'A'if j==0 else'B',font=font(17),fill='white')
    entry=next(e for r in history['frames']if r['frame']==105 for e in r['eyes']if e['owner']==2)
    dr.text((850,795),'Source-form part vectors:',font=font(16),fill='white')
    for j,v in enumerate(entry['immutableSourceFormPartVectors']):dr.text((850,830+j*30),f'{"A"if j==0 else"B"}: iris {v["1"]}, white {v["4"]}',font=font(16),fill='#ace1e7')
    dr.text((850,900),'A dominates; no new art number.',font=font(16),fill='#ffc578');dr.text((22,1005),'History agrees (source IDs, not screen RGB). Initial/mutually conflicting histories remain multiple.108 shape objective remains unadopted.',font=font(15),fill='#bbcfdf');board.save(H/'CARRIER_AND_HISTORY109.png')
    print('CARRIER_AND_HISTORY109.png')
if __name__=='__main__':main()
