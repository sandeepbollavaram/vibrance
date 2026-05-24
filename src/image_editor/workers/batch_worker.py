from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from image_editor.config import OUTPUT_SUBDIR, EditParams, ExportOptions
from image_editor.core.image_io import load_image, resize_long_edge, save_image
from image_editor.core.pipeline import process


class BatchEditWorker(QThread):
    """Runs the edit pipeline over a list of paths off the UI thread."""

    progress = Signal(int)  # 0..100
    fileDone = Signal(str, str)  # src_path, dst_path
    error = Signal(str, str)  # src_path, message

    def __init__(self, paths: list[str], params: EditParams, opts: ExportOptions):
        super().__init__()
        self._paths = list(paths)
        self._params = params
        self._opts = opts
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        total = max(len(self._paths), 1)
        for i, src in enumerate(self._paths, start=1):
            if self._cancel:
                break
            try:
                img = load_image(src)
                edited = process(img, self._params)
                if self._opts.resize_long_edge > 0:
                    edited = resize_long_edge(edited, self._opts.resize_long_edge)
                dst = self._destination(src)
                save_image(dst, edited, self._opts)
                self.fileDone.emit(src, str(dst))
            except Exception as e:  # noqa: BLE001
                self.error.emit(src, str(e))
            self.progress.emit(int(i / total * 100))

    def _destination(self, src: str) -> Path:
        src_path = Path(src)
        out_dir = (
            Path(self._opts.output_dir)
            if self._opts.output_dir
            else src_path.parent / OUTPUT_SUBDIR
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        ext = self._opts.format if self._opts.format else src_path.suffix.lstrip(".")
        return out_dir / f"{src_path.stem}{self._opts.suffix}.{ext}"
