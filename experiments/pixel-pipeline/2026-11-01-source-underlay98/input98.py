from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'native-feature89'))
from analyse89 import packet as original_packet
def packet(path):
    d=original_packet(path)
    # The source-id prefix replacement in98B also renamed this channel's file.
    # Alias its name only, retaining the marker-checked actual same-frame data.
    for i in range(4):
        name=f'current-non-eye98b-{i}'
        if name in d['a']:d['a'][f'current-non-eye98-{i}']=d['a'][name]
    return d
