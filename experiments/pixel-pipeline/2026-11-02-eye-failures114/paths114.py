from pathlib import Path
H=Path(__file__).resolve().parent
R=H.parent
NAMES={'109':('pigment-carrier109','2026-11-01-pigment-carrier109'),'110':('joint-resolver110','2026-11-01-joint-resolver110'),'22':('argon22-boundary','2026-11-01-argon22-boundary'),'111':('aperture-runtime111','2026-11-02-eye-carrier111'),'113':('argon23-runtime113','2026-11-02-argon23-runtime113')}
def folder(key):
    return next(R/n for n in NAMES[key]if(R/n).exists())
