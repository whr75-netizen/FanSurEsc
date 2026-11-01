"""Explicit Independent333 metadata schema; unrelated owner tags are not roles."""
import numpy as np
def decode_independent_meta(value):
 d,encoded,owner,alpha=map(float,value)
 if not np.isfinite([d,encoded,owner,alpha]).all()or d<=0 or alpha<=0 or encoded<1:return None
 tag=round(encoded)
 if abs(tag-encoded)>1e-5:return None
 return {'depth':d,'role':int(tag)-1,'owner':int(round(owner)),'alpha':alpha,'schema':'Independent333: depth,role+1,owner,alpha'}

def clean_skin_underlay(rgba,meta):
 """Rendered skin underlay eligibility, never a foreground eyelid decision."""
 parsed=decode_independent_meta(meta)
 if parsed is None or parsed['role']!=3 or float(rgba[3])!=1:return None
 return {'rgba':list(map(float,rgba)),'meta':parsed,'provenance':'existing same-frame Independent333 skin source','visibilityAgainstNativeLidStillRequired':True}
