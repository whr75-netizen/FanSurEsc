"""No network/generation: exercise costly side-effect boundaries and recovery."""
import base64
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
import app


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patches = [patch('app.configure', side_effect=lambda cfg: cfg),
                        patch('app.subscription_credential'),
                        patch.object(app.Coordinator, 'open_browser')]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.control = app.Coordinator({'chrome': 'unused'}, self.root)
        self.spec = dict(gpt_prompt='test image', grok_prompt='test motion', frame_count=16)

    def start_job(self):
        state = self.control.start(self.spec)
        job = self.control.jobs[state['id']]
        return job, {'id': job['id'], 'token': job['token'], 'tab_id': 1}

    def test_single_active_job_and_tab_binding(self):
        job, payload = self.start_job()
        with self.assertRaises(ValueError):
            self.control.start(self.spec)
        self.assertEqual(self.control.claim(payload)['status'], 'ready')
        with self.assertRaises(PermissionError):
            self.control.claim(dict(payload, tab_id=2))
        with self.assertRaises(PermissionError):
            self.control.claim(dict(payload, token='wrong'))

    def test_image_result_delivered_once_and_late_failure_ignored(self):
        job, payload = self.start_job()
        self.control.claim(payload)
        data = BytesIO()
        Image.new('RGB', (256, 256)).save(data, format='PNG')
        payload.update(image_base64=base64.b64encode(data.getvalue()).decode(), source_url='https://chatgpt.com/images/?secret=test')
        with patch('app.threading.Thread') as worker:
            self.control.image_result(payload)
            with self.assertRaises(ValueError):
                self.control.image_result(payload)
            self.control.event(dict(payload, stage='failed', detail='late browser message'))
            self.assertEqual(job['stage'], 'canvas')
            worker.assert_called_once()
        report = json.loads((Path(job['directory']) / 'image-report.json').read_text())
        self.assertEqual(report['page'], 'https://chatgpt.com/images/')

    def test_restart_restores_file_without_automatic_generation(self):
        job, payload = self.start_job()
        (Path(job['directory']) / 'source.png').write_bytes(b'fixture')
        persisted = json.loads((Path(job['directory']) / 'job.json').read_text())
        self.assertNotIn('token', persisted)
        with patch('app.threading.Thread') as worker:
            restored = app.Coordinator({'chrome': 'unused'}, self.root)
            self.assertEqual(restored.state()['status'], 'failed')
            self.assertTrue(restored.state()['resumable'])
            # The only thread created is the OFF-by-default local folder watcher.
            worker.assert_called_once()
            self.assertEqual(worker.call_args.kwargs['target'], restored.watch_loop)
        self.assertNotEqual(job['token'], restored.jobs[job['id']]['token'])

    def test_missing_extension_timeout_does_not_generate(self):
        job, payload = self.start_job()
        job['started_at'] = time.time() - 46
        state = self.control.state()
        self.assertEqual(state['status'], 'failed')
        self.assertFalse(state['resumable'])
        self.assertIsNone(self.control.active)


if __name__ == '__main__':
    unittest.main()
