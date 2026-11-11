from pathlib import Path
import sys
import relay33
assert sys.argv[1]in ['capture','final','console'];relay33.G=Path(__file__).resolve().parent/'face36/fix1';relay33.main()
