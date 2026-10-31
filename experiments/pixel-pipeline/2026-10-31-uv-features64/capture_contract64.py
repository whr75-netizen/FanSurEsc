"""Small packet preflight/validation; no Unity calls, files or default filling."""
REQUIRED=('sourceId','viewId','frameIndex','renderSerial','poseDigest','meshFiles','camera','grid','samples','cleanBacking','requiredBackingSampleIds','globalJournal','sourceColorSpace','gDefinition','modeFlags')
SAMPLE_REQUIRED=('sampleId','renderer','submesh','primitive','barycentric','uv','world','screen','sourceRGBA','independentG','Q','owner','depth','coverage')
def validate(packet):
 errors=[]
 for k in REQUIRED:
  if k not in packet:errors.append('missing:'+k)
 if errors:return errors
 if not packet['sourceId']or not packet['poseDigest']or not packet['viewId']:errors.append('unbound source/pose/view')
 if not packet['sourceColorSpace']or not packet['modeFlags']or not packet['gDefinition'].get('producerFunction'):errors.append('colour/shading/mode provenance missing')
 camera=packet['camera']
 for k in ('view','projection','effectiveProjection','gpuProjection','gpuEffectiveProjection'):
  if k not in camera or len(camera[k])!=16:errors.append('camera:'+k)
 grid=packet['grid']
 for k in ('logicalSize','nativeSize','viewport','clipShift','nativeShift','subsampleDefinition','yConvention'):
  if k not in grid:errors.append('grid:'+k)
 if not grid.get('subsampleDefinition',{}).get('producerFunction'):errors.append('subsample coordinates are not linked to actual producer')
 ids=set()
 if not packet['samples']or not packet['meshFiles']:errors.append('missing real sample/mesh records')
 for s in packet['samples']:
  for k in SAMPLE_REQUIRED:
   if k not in s:errors.append('sample missing:'+k)
  if s.get('sampleId')in ids:errors.append('duplicate sampleId')
  ids.add(s.get('sampleId'))
  if s.get('sourceId')!=packet['sourceId']or s.get('viewId')!=packet['viewId']or s.get('frameIndex')!=packet['frameIndex']or s.get('renderSerial')!=packet['renderSerial']:errors.append('mixed sample source/frame/serial')
  if 'barycentric'in s and abs(sum(s['barycentric'])-1)>1e-5:errors.append('barycentric sum')
 backingIds=[]
 for c in packet['cleanBacking']:
  backingIds.append(c.get('sampleId'))
  if c.get('sourceId')!=packet['sourceId']or c.get('viewId')!=packet['viewId']or c.get('frameIndex')!=packet['frameIndex']or c.get('renderSerial')!=packet['renderSerial']:errors.append('mixed clean backing source/frame/serial')
  if any(k not in c for k in ('sampleId','RGBA','owner','depth','coverage','uv','colorSpace','rgbaStage','producerPass','preEyeApplication')):errors.append('incomplete clean backing')
  if not c.get('preEyeApplication')or c.get('synthesised',False):errors.append('backing is not real pre-eye input')
 if not packet['requiredBackingSampleIds']or not set(packet['requiredBackingSampleIds']).issubset(set(backingIds)):errors.append('missing required backing destinations')
 if len(set(backingIds))!=len(backingIds):errors.append('duplicate backing sampleId')
 journal=packet['globalJournal']
 if not journal.get('externalBackupWrittenAndVerified'):errors.append('global external backup not verified')
 for mutation in journal.get('mutations',[]):
  if mutation.get('kind')in ('buffer','constant-buffer')and not mutation.get('exactOriginalBindingRecoverable'):errors.append('unbacked buffer mutation:'+mutation['name'])
  if not mutation.get('restorable'):errors.append('unrestorable mutation:'+mutation['name'])
 if journal.get('unidentifiedRendererGlobalWrites'):errors.append('renderer global writes not inventoried')
 if packet.get('largestOwnedReadbackBytes',0)>1024*1024:errors.append('readback exceeds one-MiB packet-plane bound')
 if packet.get('simultaneousReadbacks',1)>1:errors.append('more than one readback in flight')
 return errors

def require(packet):
 errors=validate(packet)
 if errors:raise ValueError('; '.join(errors))
 return packet
