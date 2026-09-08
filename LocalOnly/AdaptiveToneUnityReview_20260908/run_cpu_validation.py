"""Execute the local CPU oracle suite and write a distinct evidence summary."""
import argparse
import io
import json
from pathlib import Path
import time
import unittest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    target = args.output.resolve()
    if not target.is_relative_to(root) or target.exists():
        parser.error('Output must be a new file inside this review folder; existing files are never overwritten.')
    started = time.perf_counter()
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(root), pattern='test_*.py')
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    summary = {'stage': 'independent_cpu_oracle_and_fixture_integrity',
               'status': 'passed' if result.wasSuccessful() else 'failed',
               'tests_run': result.testsRun,
               'failures': [{'test': str(test), 'traceback': trace} for test, trace in result.failures],
               'errors': [{'test': str(test), 'traceback': trace} for test, trace in result.errors],
               'skipped': [{'test': str(test), 'reason': reason} for test, reason in result.skipped],
               'duration_seconds': time.perf_counter() - started,
               'gpu_dispatch_validation': 'not_run_by_this_script',
               'visual_design_validation': 'not_performed',
               'test_output': stream.getvalue()}
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8') as output:
        json.dump(summary, output, indent=2, allow_nan=False)
    print(json.dumps({'summary': str(target), 'status': summary['status'], 'tests_run': result.testsRun}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
