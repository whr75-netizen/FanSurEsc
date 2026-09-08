"""Known synthetic mock artifacts test the checker, not the actual GPU shader."""
import copy
import struct
import unittest

from gpu_cases import build_case, unity_flat_fixture
from validate_gpu_result import key, lab, validate


def mock_flat_artifact():
    fixture = build_case('flat_constant')
    rgb = fixture['source_color_depth'][0][:3]
    level = lab(rgb)[0]
    level_bits = struct.unpack('<I', struct.pack('<f', level))[0]
    group_key = key(rgb, fixture['source_meta'][0], fixture['settings']['chroma_error'])
    result = {'case': fixture['name'], 'width': fixture['width'], 'height': fixture['height'],
              'sourceColors': copy.deepcopy(fixture['source_color_depth']),
              'seedColors': copy.deepcopy(fixture['seed_color_depth']),
              'outputColor': copy.deepcopy(fixture['seed_color_depth']),
              'sourceMeta': copy.deepcopy(fixture['source_meta']),
              'sourceMetaBefore': copy.deepcopy(fixture['source_meta']),
              'seedMeta': copy.deepcopy(fixture['seed_meta']),
              'seedMetaBefore': copy.deepcopy(fixture['seed_meta']),
              'groups': [0] * (160 * 8), 'histogram': [0] * (160 * 32 * 6),
              'tiles': [0] * (160 * 16 * 3), 'tileHistogram': [0] * (160 * 16 * 32),
              'supports': [0] * (160 * 2), 'status': [0] * 161,
              'palette': [[0., 0., 0., 0.] for _ in range(160 * 32)],
              'solutions': [[0., 0., 0., 0.] for _ in range(160 * 3)]}
    result['groups'][:8] = [group_key, 512, 0, 0, 31, 15, level_bits, level_bits]
    result['histogram'][0] = 512
    result['histogram'][5] = 512 << 22
    result['status'][0] = 1
    result['palette'][0] = list(rgb) + [level]
    result['solutions'][0] = [1., 0., 0., 0.]
    result['solutions'][1] = [level, 0., 0., 0.]
    for tile in range(16):
        result['tiles'][tile * 3] = 32
        result['tileHistogram'][tile * 32] = 32
    return fixture, result


class GpuValidatorTests(unittest.TestCase):
    def test_known_flat_mock_passes_without_claiming_it_is_gpu_evidence(self):
        fixture, evidence = mock_flat_artifact()
        report = validate(fixture, evidence)
        self.assertEqual(report['status'], 'passed', report['checks'])
        self.assertEqual(report['stage_dp']['status'], 'passed')
        self.assertEqual(report['stage_dp']['groups'][0]['oracle_tones'], 1)

    def test_changed_depth_and_empty_seed_are_detected(self):
        fixture, evidence = mock_flat_artifact()
        evidence['outputColor'][0] = [.125, .125, .125, 2.]
        report = validate(fixture, evidence)
        self.assertEqual(report['status'], 'failed')
        self.assertTrue(any(check['check'] == 'eye_depth_and_empty_seed_values_preserved'
                            and not check['passed'] for check in report['checks']))

    def test_invented_palette_color_and_wrong_tone_count_are_detected(self):
        fixture, evidence = mock_flat_artifact()
        evidence['palette'][0][0] = .777
        evidence['solutions'][0][0] = 3
        report = validate(fixture, evidence)
        failed = {check['check'] for check in report['checks'] if not check['passed']}
        self.assertIn('palette_rgb_is_actual_group_candidate', failed)
        self.assertIn('independent_dp_minimum_candidate_count', failed)
        self.assertEqual(report['stage_dp']['status'], 'failed')

    def test_incomplete_gpu_artifact_is_not_accepted(self):
        fixture, evidence = mock_flat_artifact()
        del evidence['histogram']
        report = validate(fixture, evidence)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['stage_dp']['status'], 'not_run')

    def test_flat_jsonutility_artifact_matches_nested_array_evidence(self):
        fixture, evidence = mock_flat_artifact()
        expected = validate(fixture, evidence)
        flat = copy.deepcopy(evidence)
        flat['arrayLayout'] = 'flat_float4_v1'
        for name in ('outputColor', 'sourceColors', 'seedColors', 'sourceMetaBefore',
                     'seedMetaBefore', 'sourceMeta', 'seedMeta', 'palette', 'solutions'):
            flat[name] = [channel for row in flat[name] for channel in row]
        actual = validate(unity_flat_fixture(fixture), flat)
        self.assertEqual(actual, expected)
        flat['outputColor'].pop()
        malformed = validate(fixture, flat)
        self.assertEqual(malformed['status'], 'failed')
        self.assertEqual(malformed['checks'][0]['check'], 'flat_float4_shape')


if __name__ == '__main__':
    unittest.main()
