"""Run the suite against the same isolated dependencies as the boundary CLI."""
from pathlib import Path
import argparse
import sys
import unittest

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / '.deps'))
sys.path.insert(0, str(root / 'src'))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pattern', default='test*.py')
args = parser.parse_args()
suite = unittest.defaultTestLoader.discover(str(root / 'tests'), pattern=args.pattern)
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
