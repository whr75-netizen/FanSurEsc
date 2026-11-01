"""Producer-tagged shade labels; post-eye UV.z is intentionally NOT a Q input."""
import numpy as np
def shade_labels(plane,mask,schema,steps=2):
 if schema!='LegacySignals335.classifier_after_ShadeBoundary':raise ValueError('Wrong producer schema for shade Q')
 if not isinstance(steps,(int,np.integer)) or steps<2:raise ValueError('Explicit integer step count >=2 required')
 q=plane[...,0]
 if not np.isfinite(q[mask]).all() or np.any((q[mask]<0)|(q[mask]>1)):raise ValueError('Shade levels must stay inside [0,1]')
 ids=np.rint(q.astype(np.float64)*(steps-1)).astype(int);canonical=(ids/(steps-1)).astype(np.float32)
 ulp=np.maximum(abs(np.nextafter(canonical,np.float32(np.inf))-canonical),abs(canonical-np.nextafter(canonical,np.float32(-np.inf))))
 if np.any(np.abs(q[mask].astype(np.float64)-canonical[mask])>ulp[mask]):raise ValueError('Not a declared shade step, within one float32 ULP')
 return ids
