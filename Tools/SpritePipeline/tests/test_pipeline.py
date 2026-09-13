"""Request and paid-generation boundaries; real credentials/network stay unused."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline
from runtime import settings

sys.path.insert(0, settings()['sprite_gen_root'])
from sprite_gen.gen import video, xai


class RequestTests(unittest.TestCase):
    def test_invalid_frame_counts_are_rejected(self):
        for count in (0, -1, 17, True, False, 1.5, '16', None):
            with self.subTest(count=count), self.assertRaises(ValueError):
                pipeline.validate_request({
                    'gpt_prompt': 'character', 'grok_prompt': 'idle', 'frame_count': count,
                })

    def test_frame_count_boundaries_are_accepted(self):
        for count in (1, 16):
            self.assertEqual(pipeline.validate_request({
                'gpt_prompt': ' character ', 'grok_prompt': ' idle ', 'frame_count': count,
            }), {'mode': 'all', 'gpt_prompt': 'character', 'grok_prompt': 'idle', 'frame_count': count})


class VideoRequestTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.run_dir = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        # Canvas already exists: this suite exercises orchestration, not image work.
        (self.run_dir / 'source.png').write_bytes(b'stored-source-fixture')
        (self.run_dir / 'canvas.png').write_bytes(b'stored-canvas-fixture')
        self.spec = {'mode': 'video', 'gpt_prompt': 'character', 'grok_prompt': 'idle', 'frame_count': 16}
        self.cfg = {
            'video_duration': 6, 'video_model': 'grok-imagine-video-1.5',
            'ffmpeg': 'unused', 'ffprobe': 'unused', 'img2webp': 'unused',
            'engine_root': 'unused', 'workers': 1,
        }
        self.stack.enter_context(patch.object(pipeline, 'configure', return_value=self.cfg))
        self.resolve = self.stack.enter_context(patch.object(
            xai, 'resolve_credential',
            return_value=xai.Credential(token='unit-test-placeholder', source=xai.AUTH_SOURCE_GROK_LOGIN),
        ))
        self.http = self.stack.enter_context(patch.object(xai, 'http_json'))
        self.download = self.stack.enter_context(patch.object(
            video, 'http_download', return_value=b'\x00\x00\x00\x18ftypisom',
        ))
        self.process = self.stack.enter_context(patch(
            'postprocess.process_video', return_value={'files': {}},
        ))
        # Fail closed if a future adapter change bypasses the mocked transports.
        self.network = self.stack.enter_context(patch(
            'urllib.request.urlopen', side_effect=AssertionError('Network forbidden in this test'),
        ))
        self.notify = Mock()

    def run_pipeline(self):
        return pipeline.continue_pipeline(self.run_dir, self.spec, self.cfg, self.notify)

    def test_api_key_is_rejected_before_generation(self):
        self.resolve.return_value = xai.Credential(
            token='unit-test-placeholder', source=xai.AUTH_SOURCE_API_KEY,
        )
        with self.assertRaisesRegex(RuntimeError, 'API 키'):
            self.run_pipeline()
        self.http.assert_not_called()
        self.download.assert_not_called()
        self.process.assert_not_called()
        self.assertFalse((self.run_dir / 'video-request.json').exists())

    def test_saved_request_id_resumes_with_get_without_new_post(self):
        saved = {'submitted': True, 'request_id': 'existing-test-request'}
        pipeline.atomic_json(self.run_dir / 'video-request.json', saved)
        self.http.return_value = (200, {
            'status': 'done', 'video': {'url': 'https://example.invalid/test.mp4', 'duration': 6},
        })
        result = self.run_pipeline()
        self.assertEqual(len(self.http.call_args_list), 1)
        method, url, _, body = self.http.call_args.args
        self.assertEqual(method, 'GET')
        self.assertTrue(url.endswith('/videos/existing-test-request'))
        self.assertIsNone(body)
        self.download.assert_called_once()
        self.process.assert_not_called()
        self.network.assert_not_called()
        self.assertTrue(Path(result['files']['video']).is_file())
        self.assertEqual(json.loads((self.run_dir / 'video-request.json').read_text()), saved)

    def test_unknown_post_response_blocks_automatic_resubmission(self):
        self.http.side_effect = TimeoutError('Simulated missing POST response')
        with self.assertRaises(TimeoutError):
            self.run_pipeline()
        self.http.assert_called_once()
        self.assertEqual(self.http.call_args.args[0], 'POST')
        journal = self.run_dir / 'video-request.json'
        self.assertEqual(json.loads(journal.read_text()), {'submitted': True})

        self.http.reset_mock()
        with self.assertRaisesRegex(RuntimeError, '자동 재전송하지 않습니다'):
            self.run_pipeline()
        self.http.assert_not_called()
        self.download.assert_not_called()
        self.process.assert_not_called()
        self.network.assert_not_called()
        self.assertEqual(json.loads(journal.read_text()), {'submitted': True})


if __name__ == '__main__':
    unittest.main()
