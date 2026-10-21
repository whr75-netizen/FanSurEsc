"""Explicit sequence-state validity gate; no implicit per-model globals."""
import hashlib,json

def signature(model,projection,view,clip):
    # View translation may follow the animated head; geometry transport already
    # incorporates it. Projection/basis changes constitute a new view contract.
    basis=[view[i*4+j]for i in range(3)for j in range(3)]
    value={'model':model,'projection':projection,'viewBasis':basis,'clip':clip}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def previous_for(currentSignature,previous,seek=False):
    if previous is None:return None,'INITIAL'
    if seek:return None,'SEEK_RESET'
    if previous['signature']!=currentSignature:return None,'MODEL_CAMERA_OR_CLIP_RESET'
    return previous,'CONTINUE'
