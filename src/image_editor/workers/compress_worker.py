"""Background QThread that compresses a folder of images one by one.

Emits per-file events so the UI can update a progress bar / log without
freezing. The MainWindow owns the worker; this module is pure mechanics.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from image_editor.core.compress import save_compressed, strip_metadata


class BatchCompressWorker(QThread):
    progress = Signal(int)            # 0..100
    fileDone = Signal(str, str, float)   # src_path, dst_path, kb_saved
    error = Signal(str, str)             # src_path, message
    finishedSummary = Signal(int, int, float)   # ok, fail, total_kb_saved

    def __init__(
        self,
        files: list[str],
        out_dir: str,
        fmt: str,
        quality: int,
        target_kb: float,
        long_edge: int,
        strip_meta: bool,
        parent=None,
    ):
        super().__init__(parent)
        self.files = files
        self.out_dir = Path(out_dir)
        self.fmt = fmt if fmt and fmt != "(keep original)" else ""
        self.quality = int(quality)
        self.target_kb = float(target_kb)
        self.long_edge = int(long_edge)
        self.strip_meta = bool(strip_meta)
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        import cv2
        import numpy as np

        self.out_dir.mkdir(parents=True, exist_ok=True)
        ok = 0
        fail = 0
        total_saved_kb = 0.0
        total = max(len(self.files), 1)

        for i, src in enumerate(self.files):
            if self._cancel:
                break
            sp = Path(src)
            try:
                data = np.fromfile(str(sp), dtype=np.uint8)
                img = cv2.imdecode(data, cv2.IMREAD_COLOR)
                if img is None:
                    raise ValueError("could not decode image")
                src_size_kb = sp.stat().st_size / 1024.0

                fmt = self.fmt or sp.suffix.lstrip(".").lower() or "jpg"
                dst = self.out_dir / f"{sp.stem}_vibrance.{fmt}"

                target = self.target_kb if self.target_kb > 0 else None
                result = save_compressed(
                    dst, img,
                    target_kb=target,
                    quality=self.quality,
                    fmt=fmt,
                    max_long_edge=self.long_edge,
                )
                if self.strip_meta:
                    strip_metadata(dst)

                saved = max(0.0, src_size_kb - result.size_kb)
                total_saved_kb += saved
                ok += 1
                self.fileDone.emit(str(sp), str(dst), saved)
            except Exception as e:
                fail += 1
                self.error.emit(str(sp), str(e))

            self.progress.emit(int((i + 1) / total * 100))

        self.finishedSummary.emit(ok, fail, total_saved_kb)
