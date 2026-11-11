from pathlib import Path
import sys
import relay33
assert sys.argv[1]in ['import','capture','final','console'];relay33.G=Path(__file__).resolve().parent/'face36';relay33.main()
