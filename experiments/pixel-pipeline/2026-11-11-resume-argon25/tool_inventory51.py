from pathlib import Path
import sys
import relay33
relay33.G=Path(__file__).resolve().parent/'face51';sys.argv=[sys.argv[0],'inventory'];assert not(relay33.G/'inventory/TOOLS.json').exists();relay33.main()
