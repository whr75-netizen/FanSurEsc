"""Producer-tagged shade labels; post-eye UV.z is intentionally NOT a Q input."""
import numpy as np
def shade_labels(plane,mask,schema):
 if schema!='LegacySignals335.classifier_after_ShadeBoundary':raise ValueError('Wrong producer schema for shade Q')
 q=plane[...,0]
 if not np.isfinite(q[mask]).all() or np.any((q[mask]<0)|(q[mask]>1)):raise ValueError('Shade levels must stay inside [0,1]')
 return np.rint(q).astype(int)
