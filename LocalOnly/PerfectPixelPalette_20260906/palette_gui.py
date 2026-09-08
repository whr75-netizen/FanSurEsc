"""Local, button-driven palette comparison UI. Never overwrites the input file."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from queue import Empty, Queue
import json
import math
import re
import sys
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
from PIL import Image, ImageTk

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
APP_VERSION = "palette-lab-gui-2"
SCALE_PRESETS = ("0.1", "0.25", "0.5", "0.8", "0.9", "1.0", "1.1", "1.2", "1.5", "2.0", "3.0", "4.0")
INTEGER_SCALES = (1, 2, 3, 4, 6, 8)
MAX_DISPLAY_OR_EXPORT_PIXELS = 24_000_000
METHOD_CHOICES = {"색상 범위 (새 기본)": "color_ranges", "기존 고정 색군 (legacy)": "legacy"}


def load_engine():
    # Import lazily so this module can be inspected without launching Tk or the engine.
    from perfect_pixel import PaletteOptions, detect_base_grid, get_palette_pixel
    return PaletteOptions, detect_base_grid, get_palette_pixel


def target_dimensions(base_grid: tuple[int, int], scale: str) -> tuple[int, int]:
    # One sizing authority: minimum 1 px, scale limits and safety caps come from core.
    from perfect_pixel import scaled_grid
    return scaled_grid(base_grid, str(scale).strip())


def parse_priorities(text: str) -> tuple[tuple[str, float], ...]:
    if not text.strip():
        return tuple()
    output = []
    seen = set()
    for item in text.split(","):
        match = re.fullmatch(r"\s*(#[0-9a-fA-F]{6})\s*=\s*([^\s]+)\s*", item)
        if not match:
            raise ValueError("우선색은 #FFCCAA=2,#332211=0.5 형식으로 입력해 주세요.")
        color = match.group(1).upper()
        try:
            weight = float(match.group(2))
        except ValueError as exc:
            raise ValueError(f"{color}의 우선색 가중치가 숫자가 아닙니다.") from exc
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError("우선색 가중치는 0보다 큰 유한한 숫자여야 합니다.")
        if color in seen:
            raise ValueError(f"우선색 {color}가 중복되었습니다.")
        seen.add(color)
        output.append((color, weight))
    return tuple(output)


@dataclass(frozen=True)
class SourceSnapshot:
    path: Path
    original_bytes: bytes
    pixels: np.ndarray
    content_hash: str
    detected_base_grid: tuple[int, int] | None
    detection_warning: str | None = None


@dataclass(frozen=True)
class ProcessSnapshot:
    source: SourceSnapshot
    base_grid: tuple[int, int]
    resolution_scale: str
    target_size: tuple[int, int]
    option_values: dict


@dataclass(frozen=True)
class Comparison:
    task: ProcessSnapshot
    original_image: np.ndarray
    palette_image: np.ndarray
    original_metadata: dict
    palette_metadata: dict
    palette: np.ndarray


def decode_source(path: Path, detector) -> SourceSnapshot:
    # Read once: image bytes, pixels and provenance belong to the same file version.
    content = path.read_bytes()
    with Image.open(BytesIO(content)) as image:
        has_alpha = "A" in image.getbands() or "transparency" in image.info
        pixels = np.array(image.convert("RGBA" if has_alpha else "RGB"), dtype=np.uint8)
    detected = None
    warning = None
    try:
        proposed = tuple(detector(pixels.copy()))
        target_dimensions(proposed, "1.0")
        detected = tuple(int(v) for v in proposed)
    except Exception as exc:
        # Grid detection is optional; a readable original remains usable manually.
        warning = f"자동 격자 검출 실패 ({type(exc).__name__}: {exc}). 기준 W/H를 직접 입력해 주세요."
    pixels.setflags(write=False)
    return SourceSnapshot(path, content, pixels, sha256(content).hexdigest(), detected, warning)


def calculate_comparison(task: ProcessSnapshot, engine, options_type, cancel: threading.Event):
    options = options_type(**task.option_values)
    original = engine(task.source.pixels.copy(), base_grid=task.base_grid,
                      resolution_scale=task.resolution_scale, options=options, mode="original")
    if cancel.is_set():
        return None
    palette = engine(task.source.pixels.copy(), base_grid=task.base_grid,
                     resolution_scale=task.resolution_scale,
                     options=options_type(**task.option_values), mode="palette")
    if cancel.is_set():
        return None
    channels = task.source.pixels.shape[2]
    expected = (task.target_size[1], task.target_size[0], channels)
    for mode, result in (("original", original), ("palette", palette)):
        if not isinstance(result.image, np.ndarray) or result.image.dtype != np.uint8:
            raise TypeError(f"{mode}: 엔진 출력이 uint8 이미지가 아닙니다.")
        if result.image.shape != expected:
            raise ValueError(f"{mode}: 출력 크기 {result.image.shape}가 요청 {expected}와 다릅니다.")
    old_image = np.array(original.image, copy=True)
    new_image = np.array(palette.image, copy=True)
    colors = np.array(palette.palette, dtype=np.uint8, copy=True)
    for array in (old_image, new_image, colors):
        array.setflags(write=False)
    # Validate/copy the JSON-safe engine metadata before crossing back into Tk.
    old_metadata = json.loads(json.dumps(original.metadata, allow_nan=False))
    new_metadata = json.loads(json.dumps(palette.metadata, allow_nan=False))
    return Comparison(task, old_image, new_image, old_metadata, new_metadata, colors)


def validate_export_size(comparison: Comparison, export_scale: int) -> None:
    if isinstance(export_scale, bool) or not isinstance(export_scale, (int, np.integer)) or export_scale not in INTEGER_SCALES:
        raise ValueError("저장 확대 배율이 유효하지 않습니다.")
    for array in (comparison.original_image, comparison.palette_image):
        height, width = array.shape[:2]
        pixels = int(width) * int(height) * export_scale * export_scale
        if pixels > MAX_DISPLAY_OR_EXPORT_PIXELS:
            raise ValueError(f"저장 이미지 {width * export_scale} × {height * export_scale}가 24MP 한도를 넘습니다. 저장 확대 배율을 낮춰 주세요. 아직 파일은 만들지 않았습니다.")


def save_bundle(comparison: Comparison, parent: Path, export_scale: int) -> Path:
    # Check BOTH outputs before mkdir, copying the source, or encoding any image.
    validate_export_size(comparison, export_scale)
    task = comparison.task
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", task.source.path.stem).strip(" .")[:70] or "image"
    folder = parent / f"{stem}_palette_{datetime.now():%Y%m%d_%H%M%S_%f}"
    folder.mkdir(parents=True, exist_ok=False)
    try:
        # Exact source bytes are retained for reproducibility, not decoded/re-encoded.
        source_name = "source_original" + task.source.path.suffix.lower()
        (folder / source_name).write_bytes(task.source.original_bytes)
        files = {"source": source_name}
        for name, array in (("center_sample", comparison.original_image), ("palette", comparison.palette_image)):
            native = Image.fromarray(array)
            native_name = f"{name}.native.png"
            native.save(folder / native_name)
            files[name + "_native"] = native_name
            if export_scale > 1:
                enlarged_name = f"{name}.x{export_scale}.png"
                native.resize((native.width * export_scale, native.height * export_scale),
                              Image.Resampling.NEAREST).save(folder / enlarged_name)
                files[name + "_enlarged"] = enlarged_name
        metadata = {
            "schema": APP_VERSION,
            "created_local": datetime.now().astimezone().isoformat(),
            "source": {"original_path": str(task.source.path), "sha256": task.source.content_hash,
                       "width": task.source.pixels.shape[1], "height": task.source.pixels.shape[0],
                       "channels": task.source.pixels.shape[2], "copy_method": "original bytes unchanged"},
            "detected_base_grid": list(task.source.detected_base_grid) if task.source.detected_base_grid is not None else None,
            "grid_detection_warning": task.source.detection_warning,
            "base_grid_origin": "manual_after_detection_failure" if task.source.detected_base_grid is None else "detected" if task.base_grid == task.source.detected_base_grid else "manual_override",
            "base_grid_used": list(task.base_grid),
            "resolution_scale": task.resolution_scale,
            "target_size": list(task.target_size),
            "dimension_rule": "core scaled_grid: max(1, floor(Decimal(base_dimension) * Decimal(resolution_scale))), with core safety caps",
            "options": task.option_values,
            "export_nearest_integer_scale": export_scale,
            "palette_rgb": comparison.palette.tolist(),
            "mode_original": comparison.original_metadata,
            "mode_original_semantics": "Center-color sample on the SAME locked grid; not an unchanged upstream full-pipeline output.",
            "mode_palette": comparison.palette_metadata,
            "files": files,
            "note": "Settings belong to the last processed snapshot, not later unsaved UI edits. Native PNG is always retained.",
        }
        (folder / "reproduce.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"저장 중 오류가 발생했습니다. 생성된 일부 파일은 보존했습니다: {folder}\n{exc}") from exc
    return folder


class PreviewPane(ttk.LabelFrame):
    def __init__(self, parent, title):
        super().__init__(parent, text=title, padding=5)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.caption = ttk.Label(self, text="이미지를 불러와 주세요.", anchor="w")
        self.caption.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self.canvas = tk.Canvas(self, background="#777777", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        yscroll.grid(row=1, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        xscroll.grid(row=2, column=0, sticky="ew")
        self.canvas.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        self.photo = None

    def clear(self, text="처리 결과 대기"):
        self.photo = None
        self.canvas.delete("all")
        self.canvas.configure(scrollregion=(0, 0, 1, 1))
        self.caption.configure(text=text)

    def display(self, pixels: np.ndarray, zoom: int):
        image = Image.fromarray(pixels)
        if image.width * image.height * zoom * zoom > MAX_DISPLAY_OR_EXPORT_PIXELS:
            self.clear("미리보기 메모리 한도 초과: 출력 확대를 낮춰 주세요. 저장 크기는 그대로입니다.")
            return
        if zoom > 1:
            image = image.resize((image.width * zoom, image.height * zoom), Image.Resampling.NEAREST)
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.canvas.configure(scrollregion=(0, 0, image.width, image.height))
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.caption.configure(text=f"native {pixels.shape[1]} × {pixels.shape[0]}  |  표시 {zoom}× nearest  |  스크롤 가능")


class PaletteLab:
    def __init__(self, root: tk.Tk, engine_api):
        self.root = root
        self.options_type, self.detector, self.engine = engine_api
        self.source = None
        self.comparison = None
        self.events = Queue()
        self.job_id = 0
        self.cancel = threading.Event()
        self.closed = False
        self.base_w = tk.StringVar(value="256")
        self.base_h = tk.StringVar(value="256")
        self.scale = tk.StringVar(value="1.0")
        self.palette_method = tk.StringVar(value=next(iter(METHOD_CHOICES)))
        self.range_hue_width = tk.DoubleVar(value=15)
        self.families = tk.StringVar(value="6")
        self.tones = tk.StringVar(value="3")
        self.flatten = tk.DoubleVar(value=.75)
        self.feature = tk.DoubleVar(value=1.5)
        self.refine = tk.DoubleVar(value=.2)
        self.priorities = tk.StringVar(value="")
        self.preview_zoom = tk.StringVar(value="2")
        self.export_zoom = tk.StringVar(value="1")
        self.file_label = tk.StringVar(value="입력 이미지 없음")
        self.target_label = tk.StringVar()
        self.status = tk.StringVar(value="이미지를 불러오면 기준 격자를 한 번 검출합니다. 자동 생성은 하지 않습니다.")
        self._build_ui()
        self.palette_method.trace_add("write", self._refresh_method_controls)
        self._refresh_method_controls()
        for var in (self.base_w, self.base_h, self.scale):
            var.trace_add("write", self._refresh_target)
        self.preview_zoom.trace_add("write", lambda *_: self._redraw_outputs())
        self._refresh_target()
        self.root.after(80, self._poll)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        self.root.title("Perfect Pixel · Palette Lab (로컬)")
        self.root.geometry("1420x860")
        self.root.minsize(1080, 700)
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)
        top = ttk.Frame(outer)
        top.pack(fill="x")
        ttk.Button(top, text="이미지 불러오기", command=self.load_file).pack(side="left")
        ttk.Label(top, textvariable=self.file_label).pack(side="left", padx=12)
        settings = ttk.LabelFrame(outer, text="처리 설정 — 값 변경만으로 재생성하지 않습니다", padding=8)
        settings.pack(fill="x", pady=8)
        grid_row = ttk.Frame(settings)
        grid_row.pack(fill="x")
        ttk.Label(grid_row, text="기준 격자 W × H").pack(side="left")
        ttk.Entry(grid_row, textvariable=self.base_w, width=7).pack(side="left", padx=(8, 3))
        ttk.Label(grid_row, text="×").pack(side="left")
        ttk.Entry(grid_row, textvariable=self.base_h, width=7).pack(side="left", padx=(3, 15))
        ttk.Label(grid_row, text="해상도 scale").pack(side="left")
        ttk.Combobox(grid_row, textvariable=self.scale, values=SCALE_PRESETS, width=7).pack(side="left", padx=8)
        ttk.Label(grid_row, textvariable=self.target_label).pack(side="left", padx=8)
        method_row = ttk.Frame(settings)
        method_row.pack(fill="x", pady=8)
        ttk.Label(method_row, text="팔레트 방식").pack(side="left")
        ttk.Combobox(method_row, textvariable=self.palette_method, values=tuple(METHOD_CHOICES),
                     state="readonly", width=23).pack(side="left", padx=(6, 16))
        ttk.Label(method_row, text="색상 범위 폭 (5~60°)").pack(side="left")
        self.hue_spin = ttk.Spinbox(method_row, from_=5, to=60, increment=1,
                                   textvariable=self.range_hue_width, width=5)
        self.hue_spin.pack(side="left", padx=(6, 16))
        ttk.Label(method_row, text="기존 색군 수 (legacy 전용)").pack(side="left")
        self.family_spin = ttk.Spinbox(method_row, from_=2, to=12, textvariable=self.families, width=4)
        self.family_spin.pack(side="left", padx=(6, 14))
        ttk.Label(method_row, text="범위/색군별 톤 수").pack(side="left")
        ttk.Spinbox(method_row, from_=1, to=4, textvariable=self.tones, width=4).pack(side="left", padx=6)
        parameters = ttk.Frame(settings)
        parameters.pack(fill="x", pady=(0, 8))
        self.flatten_label = self._slider(parameters, "범주 경계 정리 (색 번짐 없음)", self.flatten, 1)
        self._slider(parameters, "작은 대비 강조", self.feature, 3)
        self._slider(parameters, "격자 정리", self.refine, .45)
        priority_row = ttk.Frame(settings)
        priority_row.pack(fill="x")
        ttk.Label(priority_row, text="우선색 (선택)").pack(side="left")
        ttk.Entry(priority_row, textvariable=self.priorities, width=42).pack(side="left", padx=8)
        ttk.Label(priority_row, text="예: #FFCCAA=2,#332211=0.5  ·  빈칸이면 자동").pack(side="left")
        command_row = ttk.Frame(outer)
        command_row.pack(fill="x", pady=(0, 8))
        self.process_button = ttk.Button(command_row, text="처리: 중앙색 / 톤·특징 비교", command=self.process, state="disabled")
        self.process_button.pack(side="left")
        ttk.Label(command_row, text="출력 미리보기 확대").pack(side="left", padx=(18, 5))
        ttk.Combobox(command_row, textvariable=self.preview_zoom, values=INTEGER_SCALES,
                     state="readonly", width=4).pack(side="left")
        ttk.Label(command_row, text="×  (출력 해상도 불변)").pack(side="left", padx=5)
        ttk.Label(command_row, text="저장 확대").pack(side="left", padx=(18, 5))
        ttk.Combobox(command_row, textvariable=self.export_zoom, values=INTEGER_SCALES,
                     state="readonly", width=4).pack(side="left")
        self.save_button = ttk.Button(command_row, text="PNG + 재현 JSON 저장", command=self.save, state="disabled")
        self.save_button.pack(side="right")
        previews = ttk.Panedwindow(outer, orient="horizontal")
        previews.pack(fill="both", expand=True)
        self.source_pane = PreviewPane(previews, "원본 — 변경 없음 / native 1×")
        self.original_pane = PreviewPane(previews, "중앙색 샘플 (동일 격자)")
        self.palette_pane = PreviewPane(previews, "톤·특징 가중")
        for pane in (self.source_pane, self.original_pane, self.palette_pane):
            previews.add(pane, weight=1)
        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(8, 0))
        self.progress = ttk.Progressbar(footer, mode="indeterminate", length=115)
        self.progress.pack(side="right", padx=(8, 0))
        ttk.Label(footer, textvariable=self.status, wraplength=1080).pack(side="left", fill="x", expand=True)

    @staticmethod
    def _slider(parent, label, var, maximum):
        caption = ttk.Label(parent, text=label)
        caption.pack(side="left")
        ttk.Scale(parent, from_=0, to=maximum, variable=var, length=115).pack(side="left", padx=4)
        readout = ttk.Label(parent, text=f"{var.get():.2f}", width=4)
        readout.pack(side="left", padx=(0, 10))
        var.trace_add("write", lambda *_: readout.configure(text=f"{var.get():.2f}"))
        return caption

    def _refresh_method_controls(self, *_):
        is_ranges = METHOD_CHOICES.get(self.palette_method.get()) == "color_ranges"
        self.hue_spin.configure(state="normal" if is_ranges else "disabled")
        self.family_spin.configure(state="disabled" if is_ranges else "normal")
        self.flatten_label.configure(text="범주 경계 정리 (색 번짐 없음)" if is_ranges else "명암 평탄화 (legacy)")

    def _refresh_target(self, *_):
        try:
            base = (int(self.base_w.get()), int(self.base_h.get()))
            width, height = target_dimensions(base, self.scale.get())
            self.target_label.set(f"출력 {width} × {height} px = max(1, floor(기준 × scale))")
        except (ValueError, tk.TclError) as exc:
            self.target_label.set(f"기준/scale 확인 (0.1~4, core 크기 한도 적용): {exc}")

    def _begin_job(self, status):
        self.cancel.set()
        self.cancel = threading.Event()
        self.job_id += 1
        self.process_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        self.progress.start(12)
        self.status.set(status)
        return self.job_id, self.cancel

    def load_file(self):
        chosen = filedialog.askopenfilename(parent=self.root, title="원본 이미지 선택",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("All files", "*.*")])
        if not chosen:
            return
        job_id, cancel = self._begin_job("이미지 읽기 및 기준 격자 1회 검출 중…")
        self.source = None
        self.comparison = None
        for pane in (self.source_pane, self.original_pane, self.palette_pane):
            pane.clear("새 이미지 불러오는 중")
        self.file_label.set(str(chosen))
        path = Path(chosen).resolve()
        detector = self.detector
        events = self.events

        def worker():
            try:
                loaded = decode_source(path, detector)
                if not cancel.is_set():
                    events.put((job_id, "loaded", loaded))
            except Exception:
                events.put((job_id, "error", traceback.format_exc()))
        threading.Thread(target=worker, daemon=True, name=f"palette-load-{job_id}").start()

    def _capture_task(self):
        if self.source is None:
            raise ValueError("먼저 이미지를 불러와 주세요.")
        base = (int(self.base_w.get()), int(self.base_h.get()))
        scale = str(Decimal(self.scale.get().strip()))
        size = target_dimensions(base, scale)
        method = METHOD_CHOICES.get(self.palette_method.get())
        if method is None:
            raise ValueError("팔레트 방식을 선택해 주세요.")
        families = int(self.families.get()) if method == "legacy" else 6
        hue_width = float(self.range_hue_width.get()) if method == "color_ranges" else 15.0
        tones = int(self.tones.get())
        if not 2 <= families <= 12 or not 1 <= tones <= 4:
            raise ValueError("색군 수는 2~12, 톤 수는 1~4 범위입니다.")
        if not math.isfinite(hue_width) or not 5 <= hue_width <= 60:
            raise ValueError("색상 범위 폭은 5~60° 범위입니다.")
        flat, feature, refine = float(self.flatten.get()), float(self.feature.get()), float(self.refine.get())
        if not (0 <= flat <= 1 and 0 <= feature <= 3 and 0 <= refine <= .45):
            raise ValueError("범주 정리/평탄화는 0~1, 대비 강조는 0~3, 격자 정리는 0~0.45 범위입니다.")
        values = dict(color_families=families, tones_per_family=tones, flatten_strength=flat,
                      palette_method=method, range_hue_width=hue_width,
                      feature_strength=feature, refine_intensity=refine,
                      color_priorities=parse_priorities(self.priorities.get()))
        self.options_type(**values).validate()
        return ProcessSnapshot(self.source, base, scale, size, values)

    def process(self):
        try:
            task = self._capture_task()
        except (ValueError, InvalidOperation, tk.TclError) as exc:
            messagebox.showerror("입력 확인", str(exc), parent=self.root)
            return
        job_id, cancel = self._begin_job(f"{task.target_size[0]} × {task.target_size[1]} · 동일 격자의 중앙색/톤·특징 처리 중…")
        events, engine, options_type = self.events, self.engine, self.options_type

        def worker():
            try:
                result = calculate_comparison(task, engine, options_type, cancel)
                if result is not None and not cancel.is_set():
                    events.put((job_id, "processed", result))
            except Exception:
                events.put((job_id, "error", traceback.format_exc()))
        threading.Thread(target=worker, daemon=True, name=f"palette-process-{job_id}").start()

    def _redraw_outputs(self):
        if self.comparison is None:
            return
        try:
            zoom = int(self.preview_zoom.get())
        except (ValueError, tk.TclError):
            return
        if zoom not in INTEGER_SCALES:
            return
        self.original_pane.display(self.comparison.original_image, zoom)
        self.palette_pane.display(self.comparison.palette_image, zoom)

    def save(self):
        if self.comparison is None:
            return
        parent = filedialog.askdirectory(parent=self.root, title="저장할 상위 폴더 — 새 결과 폴더를 만듭니다")
        if not parent:
            return
        comparison = self.comparison
        try:
            zoom = int(self.export_zoom.get())
            if zoom not in INTEGER_SCALES:
                raise ValueError("저장 확대 배율을 선택해 주세요.")
            validate_export_size(comparison, zoom)
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("저장 확인", str(exc), parent=self.root)
            return
        job_id, cancel = self._begin_job("원본 복사본 + PNG + 재현 JSON 저장 중…")
        events = self.events

        def worker():
            try:
                folder = save_bundle(comparison, Path(parent), zoom)
                events.put((job_id, "saved", folder))
            except Exception:
                events.put((job_id, "error", traceback.format_exc()))
        # Finish a user-requested write even if the window closes during encoding.
        threading.Thread(target=worker, daemon=False, name=f"palette-save-{job_id}").start()

    def _poll(self):
        if self.closed:
            return
        try:
            while True:
                job_id, kind, payload = self.events.get_nowait()
                if job_id != self.job_id:
                    continue  # An older file/job can never replace the current UI state.
                self.progress.stop()
                if kind == "loaded":
                    self.source = payload
                    if payload.detected_base_grid is not None:
                        self.base_w.set(str(payload.detected_base_grid[0]))
                        self.base_h.set(str(payload.detected_base_grid[1]))
                    else:
                        self.base_w.set("")
                        self.base_h.set("")
                    self.source_pane.display(payload.pixels, 1)
                    self.original_pane.clear()
                    self.palette_pane.clear()
                    if payload.detection_warning:
                        self.status.set(f"원본은 정상적으로 불러왔습니다. {payload.detection_warning}")
                    else:
                        self.status.set(f"기준 격자 {payload.detected_base_grid[0]} × {payload.detected_base_grid[1]} 검출 완료. 수정 가능하며 scale 변경은 기준을 바꾸지 않습니다. [처리]를 눌러 주세요.")
                elif kind == "processed":
                    self.comparison = payload
                    self._redraw_outputs()
                    self.status.set(f"처리 완료 · base {payload.task.base_grid[0]} × {payload.task.base_grid[1]} · scale {payload.task.resolution_scale} · 팔레트 {len(payload.palette)}색. 표시/저장은 마지막 처리값 기준입니다.")
                elif kind == "saved":
                    self.status.set(f"저장 완료: {payload}")
                    messagebox.showinfo("저장 완료", f"원본은 변경하지 않았습니다.\n{payload}", parent=self.root)
                elif kind == "error":
                    print(payload, file=sys.stderr)
                    self.status.set("작업 실패. 기존 원본/처리 결과는 보존했습니다. 오류 내용을 확인해 주세요.")
                    messagebox.showerror("Palette Lab 오류", str(payload)[-5000:], parent=self.root)
                self.process_button.configure(state="normal" if self.source is not None else "disabled")
                self.save_button.configure(state="normal" if self.comparison is not None else "disabled")
        except Empty:
            pass
        self.root.after(80, self._poll)

    def close(self):
        self.closed = True
        self.cancel.set()
        self.root.destroy()


def main() -> int:
    try:
        engine_api = load_engine()
        root = tk.Tk()
        PaletteLab(root, engine_api)
        root.mainloop()
        return 0
    except Exception:
        traceback.print_exc()
        print("\n실행 실패: Tkinter, Pillow, numpy 및 로컬 src/perfect_pixel API를 확인해 주세요. 자동 설치는 하지 않습니다.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
