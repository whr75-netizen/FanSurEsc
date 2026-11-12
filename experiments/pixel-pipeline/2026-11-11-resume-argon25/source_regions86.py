"""Source-support regions, independent of quantized colour-parent addresses.

CC4 is an exact discrete partition of already observed support, not a claim that
diagonal/crossing strokes or every region share one pigment/reference colour.
"""
import numpy as np
def connected4(mask):
 m=np.asarray(mask,bool)
 if m.ndim!=2 or m.size>1100000:raise ValueError('bounded native support')
 h,w=m.shape;parent=[];runs=[];previous=[]
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def union(a,b):
  a=root(a);b=root(b)
  if a!=b:parent[max(a,b)]=min(a,b)
 for y in range(h):
  change=np.diff(np.r_[False,m[y],False].astype(np.int8));starts=np.flatnonzero(change==1);ends=np.flatnonzero(change==-1)-1;current=[];j=0
  for lo,hi in zip(starts,ends):
   i=len(parent);parent.append(i);lo=int(lo);hi=int(hi);current.append((lo,hi,i));runs.append((y,lo,hi,i))
   while j<len(previous)and previous[j][1]<lo:j+=1
   k=j
   while k<len(previous)and previous[k][0]<=hi:union(i,previous[k][2]);k+=1
  previous=current
 roots=sorted({root(i)for i in range(len(parent))});ids={v:i+1 for i,v in enumerate(roots)};labels=np.zeros(m.shape,np.int32)
 for y,lo,hi,i in runs:labels[y,lo:hi+1]=ids[root(i)]
 return labels,len(roots)

def partition(mask,foreground):
 mask=np.asarray(mask,bool);fg=np.asarray(foreground,bool)
 if fg.shape!=mask.shape or(fg&~mask).any():raise ValueError('only observed supported pigment may enter')
 island,ni=connected4(mask);pigment,nf=connected4(fg);base,nb=connected4(mask&~fg);regions=np.where(fg,pigment,base+nf);regions[~mask]=0
 return {'regions':regions,'pigment':pigment,'base':base,'island':island,'foreground':fg,'mask':mask,'pigmentCount':nf,'baseCount':nb,'islandCount':ni}

def colour_fields(rgb,part):
 rgb=np.asarray(rgb);labels=part['regions'];mask=part['mask'];n=int(labels.max())+1;flat=labels[mask];values=rgb[mask].astype(float);yy,xx=np.indices(mask.shape);x=xx[mask].astype(float)/max(1,mask.shape[1]-1);y=yy[mask].astype(float)/max(1,mask.shape[0]-1)
 counts=np.bincount(flat,minlength=n);mins=np.full((n,3),255.);maxs=np.zeros((n,3));np.minimum.at(mins,flat,values);np.maximum.at(maxs,flat,values)
 # Sufficient statistics of affine encoded-RGB fields. Fitting never emits RGB.
 basis=np.stack([np.ones(len(x)),x,y],1);s=np.zeros((n,3,3));t=np.zeros((n,3,3))
 for i in range(3):
  for j in range(3):np.add.at(s[:,i,j],flat,basis[:,i]*basis[:,j]);np.add.at(t[:,i,j],flat,basis[:,i]*values[:,j])
 coef=np.zeros_like(t);rank=np.zeros(n,int)
 for k in range(1,n):
  rank[k]=np.linalg.matrix_rank(s[k]);coef[k]=np.linalg.pinv(s[k])@t[k]
 predicted=np.einsum('ni,nij->nj',basis,coef[flat]);err=np.max(abs(predicted-values),1);maximum=np.zeros(n);np.maximum.at(maximum,flat,err);rows=[]
 for k in range(1,n):rows.append({'id':k,'texels':int(counts[k]),'kind':'pigment-support'if k<=part['pigmentCount']else'base-support','RGBMin':mins[k].astype(int).tolist(),'RGBMax':maxs[k].astype(int).tolist(),'exactConstantRGB':bool(np.array_equal(mins[k],maxs[k])),'affineEncodedRGBMaxCodeResidual':float(maximum[k]),'affineRank':int(rank[k]),'affineWithinNativeHalfCodeInterval':bool(counts[k]>3 and rank[k]==3 and maximum[k]<=.5),'authorSemanticOrMatteKnown':False})
 return rows
