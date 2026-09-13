"""Machine-local dependencies; no service credentials are stored here."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parents[1]
DEFAULT_TRIAL = Path.home() / '.codex/visualizations/2026/09/10/01a08c0e-bbf2-7d10-b1e8-607c2c27f6d3/sprite-gen-trial'
RUNS_ROOT = PROJECT_ROOT / 'LocalOnly/SpritePipelineRuns'


def settings() -> dict:
    cfg = {
        'trial_root': str(DEFAULT_TRIAL),
        'sprite_gen_root': str(Path.home() / '.codex/skills/sprite-gen'),
        'engine_root': str(PROJECT_ROOT / 'LocalOnly/PerfectPixelPalette_20260906'),
        'image_provider': 'chatgpt-browser-subscription',
        'video_model': 'grok-imagine-video-1.5',
        'video_duration': 6,
        'workers': min(4, max(1, os.cpu_count() or 1)),
        'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    }
    path = APP_ROOT / 'settings.local.json'
    if path.exists():
        cfg.update(json.loads(path.read_text(encoding='utf-8')))
    return cfg


def configure(cfg: dict | None = None) -> dict:
    cfg = cfg or settings()
    trial = Path(cfg['trial_root'])
    cfg['ffmpeg'] = str(trial / 'tools/ffmpeg/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe')
    cfg['ffprobe'] = str(trial / 'tools/ffmpeg/ffmpeg-9.0.1-essentials_build/bin/ffprobe.exe')
    cfg['img2webp'] = str(trial / 'tools/webp/libwebp-1.6.0-windows-x64/bin/img2webp.exe')
    for path in (Path(cfg['sprite_gen_root']), Path(cfg['engine_root']) / 'src'):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    for key in ('ffmpeg', 'ffprobe', 'img2webp'):
        if not Path(cfg[key]).is_file():
            raise RuntimeError(f'필요한 실행 파일이 없습니다: {key} — {cfg[key]}')
    os.environ['PATH'] = os.pathsep.join([
        str(Path(cfg['ffmpeg']).parent), str(Path(cfg['img2webp']).parent),
        os.environ.get('PATH', ''),
    ])
    return cfg
