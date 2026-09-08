"""Thin capture adapter: all image processing belongs to the shared CLI.

The pre-fix 64-color adapter/config are preserved in Git commit b371466.
No failure handler may substitute global color clustering for region tones.
"""
from pathlib import Path
import argparse
import runpy
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
ENGINE = ROOT.parent / 'PerfectPixelPalette_20260906'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'review_config.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'result_highlight_layers_96')
    args = parser.parse_args()
    cli = runpy.run_path(str(ENGINE / 'trigger_cli.py'))
    cli['main'](['--config', str(args.config), '--output', str(args.output)])


if __name__ == '__main__':
    main()
