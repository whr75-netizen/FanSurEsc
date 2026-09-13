"""Deterministic selected-frame processing; no model calls or visual scoring.

The original PerfectPixel and sprite-gen engines remain the algorithm owners.
Only selected frames are decoded to PNG, keyed, and sampled. This is a new-run
policy, not a reproduction of the previously approved full-video crop.
"""
from __future__ import annotations

import bisect
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import nullcontext
from fractions import Fraction
import json
import math
import multiprocessing
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import numpy as np
from PIL import Image


def select_frames(timestamps: list[float], duration: float, count: int) -> list[int]:
    """Sample the displayed frame at k*T/N; the endpoint T is excluded."""
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 16:
        raise ValueError("Frame count must be an integer between 1 and 16.")
    if not math.isfinite(duration) or duration <= 0 or not timestamps:
        raise ValueError("The video needs finite timestamps and a positive duration.")
    if any(not math.isfinite(t) for t in timestamps):
        raise ValueError("The video has a non-finite presentation timestamp.")
    if timestamps[0] != 0 or any(b < a for a, b in zip(timestamps, timestamps[1:])):
        raise ValueError("Presentation timestamps must start at zero and be ordered.")
    if timestamps[-1] >= duration:
        raise ValueError("Video duration must include the final frame's display interval.")
    indices = [bisect.bisect_right(timestamps, k * duration / count) - 1 for k in range(count)]
    if len(set(indices)) != count:
        raise ValueError("The requested phases do not select distinct source frames; reduce frame count.")
    return indices


def common_crop(bounds: list[tuple[int, int, int, int]], width: int):
    """Align one union crop to the exact 512/W scale and add two logical pixels."""
    if width < 512 or not bounds:
        raise ValueError("A square source of at least 512 pixels and visible foreground are required.")
    scale = Fraction(512, width)
    step, pad = scale.denominator, Fraction(2, 1) / scale
    union = (min(b[0] for b in bounds), min(b[1] for b in bounds),
             max(b[2] for b in bounds), max(b[3] for b in bounds))
    if any(not 0 <= value <= width for value in union) or union[0] >= union[2] or union[1] >= union[3]:
        raise ValueError("Foreground bounds are outside the square source.")
    left = max(0, math.floor((union[0] - pad) / step) * step)
    top = max(0, math.floor((union[1] - pad) / step) * step)
    right = min(width, math.ceil((union[2] + pad) / step) * step)
    bottom = min(width, math.ceil((union[3] + pad) / step) * step)
    crop = (left, top, right, bottom)
    grid = (int((right - left) * scale), int((bottom - top) * scale))
    return crop, grid, scale, union


def _run(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"{Path(command[0]).name} failed ({result.returncode}): {result.stderr[-2500:]}")
    return result.stdout


def probe_video(clip: Path, ffprobe: Path) -> dict:
    data = json.loads(_run([
        str(ffprobe), "-v", "error", "-select_streams", "v:0", "-show_frames",
        "-show_entries", "stream=width,height,duration:frame=best_effort_timestamp_time,pkt_duration_time,duration_time",
        "-of", "json", str(clip),
    ]))
    streams, frames = data.get("streams", []), data.get("frames", [])
    if not streams or not frames:
        raise ValueError("The input has no decodable video frames.")
    stream = streams[0]
    width, height = int(stream["width"]), int(stream["height"])
    if width != height or width < 512:
        raise ValueError(f"Expected square video >=512px; got {width}x{height}. No implicit resize is applied.")
    try:
        pts = [float(frame["best_effort_timestamp_time"]) for frame in frames]
        origin = pts[0]
        times = [t - origin for t in pts]
        last_interval = float(frames[-1].get("duration_time", frames[-1].get("pkt_duration_time", 0)))
        duration = float(stream.get("duration", 0))
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Cannot establish the video's presentation timeline.") from error
    if last_interval > 0:
        duration = max(duration, times[-1] + last_interval)
    if not math.isfinite(duration) or duration <= times[-1]:
        raise ValueError("The final display interval is missing; no guessed frame rate is used.")
    return {"width": width, "height": height, "duration_seconds": duration,
            "timestamps_seconds": times, "presentation_origin_seconds": origin}


def _key_frame(index: int, path: str, key: str):
    from sprite_gen.frames.cutout import extract_route

    started = perf_counter()
    with Image.open(path) as image:
        keyed, details = extract_route(image.convert("RGBA"), key)
    rgba = np.array(keyed, dtype=np.uint8)
    rgba[..., 3] = np.where(rgba[..., 3] >= 128, 255, 0).astype(np.uint8)
    rgba[rgba[..., 3] == 0] = 0
    bounds = Image.fromarray(rgba[..., 3]).getbbox()
    if bounds is None:
        raise ValueError(f"Selected frame {index} contains no foreground after keying.")
    if not np.any(rgba[..., 3] == 0):
        raise ValueError(f"Selected frame {index} has no removable key background.")
    return index, rgba, bounds, details, perf_counter() - started


def _engine_import(engine_root: str):
    source = str(Path(engine_root) / "src")
    if source not in sys.path:
        sys.path.insert(0, source)
    from perfect_pixel.trigger_pipeline import sample_scoped, source_palette
    return sample_scoped, source_palette


def _sample_frame(index: int, rgba: np.ndarray, crop: tuple, grid: tuple, engine_root: str):
    started = perf_counter()
    sample_scoped, _ = _engine_import(engine_root)
    left, top, right, bottom = crop
    source = np.ascontiguousarray(rgba[top:bottom, left:right])
    sampled = sample_scoped(
        source, grid, np.ones(source.shape[:2], dtype=bool), coverage=.5,
        method="source_regions", source_guide=source, color_edge_threshold=.08,
    )
    return index, sampled, perf_counter() - started


def _pool_context(pool, workers, count):
    if pool is not None:
        return nullcontext(pool)
    return ProcessPoolExecutor(max_workers=min(workers, count),
                               mp_context=multiprocessing.get_context("spawn"))


def prepare_frames(clip: Path, out: Path, frame_count: int, *, ffmpeg: Path,
                   ffprobe: Path, key="green", workers=4, on_progress=None,
                   _pool=None) -> dict:
    """Extract/key selected frames and save a reusable manifest; no pixel stage."""
    started = perf_counter()
    clip, out = Path(clip).resolve(), Path(out).resolve()
    if out.exists():
        raise FileExistsError(f"Output already exists; previous results are preserved: {out}")
    if key not in ("green", "magenta"):
        raise ValueError("The automated pipeline requires an explicit green or magenta chroma background.")
    if isinstance(workers, bool) or not isinstance(workers, int) or not 1 <= workers <= 16:
        raise ValueError("Worker count must be an integer between 1 and 16.")
    for path in (clip, Path(ffmpeg), Path(ffprobe)):
        if not path.is_file():
            raise FileNotFoundError(path)
    timings = {}

    def notify(stage, detail):
        if on_progress:
            on_progress(stage, detail)

    notify("probe", "Reading presentation timestamps")
    stage_start = perf_counter()
    video = probe_video(clip, Path(ffprobe))
    duration = video["duration_seconds"]
    selected = select_frames(video["timestamps_seconds"], duration, frame_count)
    timings["probe"] = perf_counter() - stage_start
    out.mkdir(parents=True, exist_ok=False)
    raw_dir, frames_dir = out / "source-frames", out / "keyed"
    raw_dir.mkdir()
    frames_dir.mkdir()
    notify("extract", f"Extracting only {frame_count} selected frames")
    stage_start = perf_counter()
    expression = "+".join(f"eq(n\\,{index})" for index in selected)
    _run([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(clip),
          "-map", "0:v:0", "-vf", "select=" + expression, "-fps_mode", "vfr",
          "-frames:v", str(frame_count), "-start_number", "0", "-threads", "1",
          str(raw_dir / "frame-%02d.png")])
    raw_paths = [raw_dir / f"frame-{index:02}.png" for index in range(frame_count)]
    if not all(path.is_file() for path in raw_paths):
        raise RuntimeError("FFmpeg did not emit the requested selected frames.")
    timings["extract"] = perf_counter() - stage_start
    key_details, worker_key_seconds = {}, {}
    keyed_paths = [frames_dir / f"frame-{i:02d}.png" for i in range(frame_count)]
    bounds = [None] * frame_count
    with _pool_context(_pool, workers, frame_count) as pool:
        stage_start = perf_counter()
        pending = [pool.submit(_key_frame, i, str(path), key) for i, path in enumerate(raw_paths)]
        for completed, future in enumerate(as_completed(pending), 1):
            index, rgba, bbox, details, elapsed = future.result()
            Image.fromarray(rgba).save(keyed_paths[index])
            bounds[index] = bbox
            key_details[index], worker_key_seconds[index] = details, elapsed
            notify("key", f"Background removed: {completed}/{frame_count}")
        timings["key_including_pool_start"] = perf_counter() - stage_start
    crop, grid, scale, union = common_crop(bounds, video["width"])
    timings["total"] = perf_counter() - started
    manifest_path = out / "manifest.json"
    result = {
        "schema": "sprite-prepared-frames-v1", "source_video": str(clip),
        "frame_count": frame_count, "source_size": [video["width"], video["height"]],
        "duration_seconds": duration, "frame_durations_seconds": [duration / frame_count] * frame_count,
        "common_crop_xyxy": list(crop), "cell_size": list(grid), "uniform_scale": str(scale),
        "selected_foreground_union_xyxy": list(union), "key": key,
        "timings_seconds": timings, "worker_key_seconds": worker_key_seconds, "key_details": key_details,
        "files": {"manifest": str(manifest_path), "keyed_frames": [str(p) for p in keyed_paths]},
        "frames": [{"file": f"keyed/{path.name}", "source_frame_zero_based": selected[i],
                    "source_time_seconds": video["timestamps_seconds"][selected[i]],
                    "target_time_seconds": i * duration / frame_count}
                   for i, path in enumerate(keyed_paths)],
    }
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    notify("prepared", f"{frame_count} reusable RGBA frames saved")
    return result


def pixel_frames(prepared, out: Path, *, img2webp: Path, engine_root: Path,
                 duration=1.0, workers=4, on_progress=None, _pool=None) -> dict:
    """Pixelize a prepared manifest or external RGBA PNG list.

    For external images, duration is the whole cycle in seconds, or a list of
    per-frame seconds. A prepared manifest owns its saved timeline and crop.
    """
    started = perf_counter()
    out, engine_root = Path(out).resolve(), Path(engine_root).resolve()
    if out.exists():
        raise FileExistsError(f"Output already exists; previous results are preserved: {out}")
    manifest = None
    if isinstance(prepared, dict):
        prepared = prepared["files"]["manifest"]
    if isinstance(prepared, (str, Path)):
        manifest_path = Path(prepared).resolve()
        if manifest_path.is_dir():
            manifest_path /= "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        paths = [(manifest_path.parent / frame["file"]).resolve() for frame in manifest["frames"]]
    else:
        paths = [Path(path).resolve() for path in prepared]
    frame_count = len(paths)
    if not 1 <= frame_count <= 16:
        raise ValueError("Provide between 1 and 16 RGBA PNG frames in animation order.")
    frame_seconds = (manifest["frame_durations_seconds"] if manifest else
                     list(duration) if isinstance(duration, (list, tuple)) else [float(duration) / frame_count] * frame_count)
    if len(frame_seconds) != frame_count or any(not math.isfinite(t) or t <= 0 for t in frame_seconds):
        raise ValueError("Each frame needs a positive finite duration.")
    total_duration = sum(frame_seconds)
    source_frames, bounds, source_size = [], [], None
    for path in paths:
        with Image.open(path) as image:
            if image.format != "PNG" or image.mode != "RGBA":
                raise ValueError(f"Expected an RGBA PNG with alpha: {path.name}")
            if image.width != image.height or image.width < 512 or (source_size and image.size != source_size):
                raise ValueError("All source frames must have the same square size of at least 512 pixels.")
            source_size = image.size
            rgba = np.array(image)
        rgba[..., 3] = np.where(rgba[..., 3] >= 128, 255, 0).astype(np.uint8)
        rgba[rgba[..., 3] == 0] = 0
        bbox = Image.fromarray(rgba[..., 3]).getbbox()
        if bbox is None:
            raise ValueError(f"Frame has no visible foreground: {path.name}")
        bounds.append(bbox)
        source_frames.append(rgba)
    if manifest:
        crop, grid = tuple(manifest["common_crop_xyxy"]), tuple(manifest["cell_size"])
        scale = Fraction(manifest["uniform_scale"])
        union = tuple(manifest["selected_foreground_union_xyxy"])
        source_records = manifest["frames"]
    else:
        crop, grid, scale, union = common_crop(bounds, source_size[0])
        source_records = [{"source_frame_zero_based": i, "source_time_seconds": sum(frame_seconds[:i]),
                           "target_time_seconds": sum(frame_seconds[:i])} for i in range(frame_count)]
    out.mkdir(parents=True, exist_ok=False)
    frames_dir = out / "frames"
    frames_dir.mkdir()
    timings, worker_sample_seconds = {}, {}
    sampled = [None] * frame_count

    def notify(stage, detail):
        if on_progress:
            on_progress(stage, detail)

    stage_start = perf_counter()
    with _pool_context(_pool, workers, frame_count) as pool:
        pending = [pool.submit(_sample_frame, i, rgba, crop, grid, str(engine_root))
                   for i, rgba in enumerate(source_frames)]
        for completed, future in enumerate(as_completed(pending), 1):
            index, pixels, elapsed = future.result()
            sampled[index], worker_sample_seconds[index] = pixels, elapsed
            notify("pixel", f"PerfectPixel sampling: {completed}/{frame_count}")
        timings["sample"] = perf_counter() - stage_start
    del source_frames
    notify("palette", "Applying one shared palette to all selected frames")
    stage_start = perf_counter()
    _, source_palette = _engine_import(str(engine_root))
    joined = np.concatenate(sampled, axis=0)
    colored, palette = source_palette(joined, np.ones(joined.shape[:2], bool), colors=64, iterations=3)
    timings["palette"] = perf_counter() - stage_start
    notify("export", "Writing the sprite sheet and animation previews")
    stage_start = perf_counter()
    frames, frame_files = [], []
    for index in range(frame_count):
        pixels = colored[index * grid[1]:(index + 1) * grid[1]].copy()
        pixels[pixels[..., 3] == 0] = 0
        frame = Image.fromarray(pixels)
        path = frames_dir / f"frame-{index:02d}.png"
        frame.save(path)
        frames.append(frame)
        frame_files.append(path)
    sheet = Image.new("RGBA", (grid[0] * frame_count, grid[1]))
    for index, frame in enumerate(frames):
        sheet.paste(frame, (index * grid[0], 0))
    sheet_path, gif_path, webp_path = (out / f"animation.{ext}" for ext in ("png", "gif", "webp"))
    sheet.save(sheet_path)
    from sprite_gen.util.gif_utils import _prepare_transparent_frame

    gif_durations = [max(10, round(seconds * 100) * 10) for seconds in frame_seconds]
    gif_frames = [_prepare_transparent_frame(frame, 128) for frame in frames]
    gif_frames[0].save(gif_path, save_all=True, append_images=gif_frames[1:],
                       duration=gif_durations, loop=0, disposal=2, transparency=255)
    ticks = [round(sum(frame_seconds[:k]) * 1000) for k in range(frame_count + 1)]
    durations = [b - a for a, b in zip(ticks, ticks[1:])]
    if min(durations) <= 0:
        raise ValueError("The selected frame duration is below the WebP millisecond clock.")
    command = [str(img2webp), "-loop", "0"]
    for path, milliseconds in zip(frame_files, durations):
        command.extend(["-d", str(milliseconds), "-lossless", "-exact", str(path)])
    command.extend(["-o", str(webp_path)])
    _run(command)
    timings["export"] = perf_counter() - stage_start
    # Save completion is sufficient here; no output re-decoding or art checks.
    metadata_path, report_path = out / "animation.json", out / "report.json"
    metadata = {
        "image": sheet_path.name, "frame_count": frame_count, "cell_size": list(grid),
        "size": list(sheet.size), "duration_seconds": total_duration, "loop": True,
        "frame_durations_seconds": frame_seconds, "palette": palette["palette"],
        "coordinates": {"origin": "top-left pixel edge", "x": "right", "y": "down",
                        "units": "px", "canonical_canvas": [512, 512], "source_size": list(source_size),
                        "common_crop_xyxy": list(crop), "selected_foreground_union_xyxy": list(union),
                        "uniform_scale": str(scale), "formula": "q = scale * (p - crop_origin)",
                        "source_cell_edges": "ceil(j * source_length / target_length - 0.5)",
                        "padding": "2 logical pixels, rounded outward to the scale-denominator lattice; clipped at canvas edges"},
        "pivot_pixels": [float((Fraction(source_size[0], 2) - crop[0]) * scale), float((union[3] - crop[1]) * scale)],
        "pivot_meaning": "Fixed canvas horizontal center and selected union bottom; not tracked feet",
        "frames": [{"index": i, "file": f"frames/{path.name}",
                    "source_frame_zero_based": source_records[i]["source_frame_zero_based"],
                    "source_time_seconds": source_records[i]["source_time_seconds"],
                    "target_time_seconds": source_records[i]["target_time_seconds"],
                    "duration_seconds": frame_seconds[i],
                    "webp_duration_ms": durations[i], "rect": {"x": i * grid[0], "y": 0, "w": grid[0], "h": grid[1]}}
                   for i, path in enumerate(frame_files)],
        "previews": {"gif_frame_durations_ms": gif_durations, "gif_total_ms": sum(gif_durations),
                     "webp_total_ms": sum(durations),
                     "identical_frame_merging_allowed": True, "native_png_and_atlas_count_are_authoritative": True},
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    timings["total"] = perf_counter() - started
    files = {"sheet": str(sheet_path), "gif": str(gif_path), "webp": str(webp_path),
             "metadata": str(metadata_path), "report": str(report_path), "frames": [str(p) for p in frame_files]}
    result = {"files": files, "timings_seconds": timings, "frame_count": frame_count,
              "cell_size": list(grid), "duration_seconds": total_duration,
              "source_video": manifest.get("source_video") if manifest else None,
              "source_frames": [str(path) for path in paths],
              "workers": min(workers, frame_count), "worker_sample_seconds": worker_sample_seconds,
              "policy": {"frame_selection": "saved manifest order or supplied PNG list order",
                         "crop": "selected-frame union; new runs only", "alpha": "binary >=128",
                         "sampling": "original PerfectPixel source_regions, coverage .5, Oklab edge .08",
                         "palette": "original source_palette, shared 64 colors, 3 iterations",
                         "ai_calls": 0, "visual_status": "awaiting user review", "loop_seam_guaranteed": False},
              "status": "saved"}
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    notify("done", f"{frame_count} frames exported in {timings['total']:.2f}s")
    return result


def process_video(clip: Path, out: Path, frame_count: int, *, ffmpeg: Path,
                  ffprobe: Path, img2webp: Path, engine_root: Path, key="green",
                  workers=4, on_progress=None) -> dict:
    """Run both reusable stages with one worker pool and no intervening AI."""
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError(f"Output already exists; previous results are preserved: {out}")
    started = perf_counter()
    with _pool_context(None, workers, frame_count) as pool:
        prepared = prepare_frames(clip, out / "prepared", frame_count, ffmpeg=ffmpeg,
                                  ffprobe=ffprobe, key=key, workers=workers,
                                  on_progress=on_progress, _pool=pool)
        result = pixel_frames(prepared["files"]["manifest"], out / "pixel",
                              img2webp=img2webp, engine_root=engine_root,
                              workers=workers, on_progress=on_progress, _pool=pool)
    result["files"]["prepared_manifest"] = prepared["files"]["manifest"]
    result["timings_seconds"] = {**prepared["timings_seconds"], **result["timings_seconds"],
                                "total": perf_counter() - started}
    Path(result["files"]["report"]).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
