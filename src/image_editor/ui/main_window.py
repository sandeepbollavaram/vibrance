from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from image_editor.config import (
    APP_ID,
    APP_NAME,
    APP_ORG,
    OUTPUT_SUBDIR,
    SUPPORTED_EXTS,
    EditParams,
    ExportOptions,
)
from image_editor.core import History, load_image
from image_editor.core.compress import save_compressed, strip_metadata
from image_editor.core.image_io import resize_long_edge
from image_editor.core.pipeline import process
from image_editor.ui.widgets.batch_dialog import BatchDialog
from image_editor.ui.widgets.compressor_panel import CompressorPanel
from image_editor.ui.widgets.crop_dialog import CropDialog
from image_editor.ui.widgets.drop_zone import DropZone
from image_editor.ui.widgets.edit_panel import EditPanel
from image_editor.ui.widgets.split_compare import SplitCompareWidget
from image_editor.ui.widgets.toast import show_toast
from image_editor.ui.widgets.tool_rail import ToolRail
from image_editor.ui.widgets.zoom_bar import ZoomBar
from image_editor.ui.widgets.zoomable_view import ZoomableImageView
from image_editor.utils.logger import get_logger
from image_editor.workers.batch_worker import BatchEditWorker
from image_editor.workers.compress_worker import BatchCompressWorker


def _bgr_to_pixmap(bgr: np.ndarray) -> QPixmap:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(img)


class _CanvasArea(QFrame):
    """Wraps the preview/empty-state stack and accepts drag-and-drop. Forwards
    accepted file drops via ``fileDropped(path)`` to the main window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Canvas")
        self.setAcceptDrops(True)
        self._highlight = False

    fileDropped = None  # bound by MainWindow

    def dragEnterEvent(self, e):  # noqa: N802
        if e.mimeData().hasUrls() and self._accept(e.mimeData().urls()):
            e.acceptProposedAction()
            self._highlight = True
            self.setStyleSheet(
                "QFrame#Canvas { border: 2px dashed #5AB0FF; background-color: #0E1A2E; }"
            )
        else:
            e.ignore()

    def dragLeaveEvent(self, e):  # noqa: N802
        self._highlight = False
        self.setStyleSheet("")

    def dropEvent(self, e):  # noqa: N802
        self._highlight = False
        self.setStyleSheet("")
        for u in e.mimeData().urls():
            p = Path(u.toLocalFile())
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                if callable(self.fileDropped):
                    self.fileDropped(str(p))
                e.acceptProposedAction()
                return
        e.ignore()

    def _accept(self, urls) -> bool:
        for u in urls:
            p = Path(u.toLocalFile())
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                return True
        return False


class MainWindow(QMainWindow):
    PREVIEW_DEBOUNCE_MS = 80
    THUMB_DEBOUNCE_MS = 350
    RECENT_LIMIT = 8

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1680, 980)
        self.setAcceptDrops(True)

        self.log = get_logger()
        self.history = History()  # internal undo/redo — no visible panel
        self._settings = QSettings(APP_ORG, APP_ID)
        self._recent: list[str] = self._load_recent()

        self._current_image: np.ndarray | None = None
        self._current_path: str | None = None
        self._preview_image: np.ndarray | None = None
        self._compare_window: SplitCompareWidget | None = None
        self._worker: BatchEditWorker | None = None
        self._batch_dialog: BatchDialog | None = None

        self._build_ui()
        self._build_menu()
        self._wire_shortcuts()

        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._render_preview)

        self._thumb_timer = QTimer(self)
        self._thumb_timer.setSingleShot(True)
        self._thumb_timer.timeout.connect(self._refresh_thumbnails)

        self.statusBar().showMessage("Ready · drag & drop an image to begin")

    # ----- build -------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # === LEFT: tool rail ===
        self.tool_rail = ToolRail()
        self.tool_rail.toolChanged.connect(self._on_tool_changed)
        root.addWidget(self.tool_rail, 0)

        # === CENTER: canvas stack (drop-zone / preview) + zoom bar ===
        center = QVBoxLayout()
        center.setSpacing(10)
        center.setContentsMargins(0, 0, 0, 0)

        self.canvas = _CanvasArea()
        self.canvas.fileDropped = self._open_path
        canvas_layout = QVBoxLayout(self.canvas)
        canvas_layout.setContentsMargins(10, 10, 10, 10)
        canvas_layout.setSpacing(0)

        # Stack: 0 = empty state (drop zone), 1 = preview
        self.canvas_stack = QStackedWidget()
        self.drop_zone = DropZone()
        self.drop_zone.fileDropped.connect(self._open_path)
        self.drop_zone.openRequested.connect(self._action_open)
        self.canvas_stack.addWidget(self.drop_zone)

        self.preview_view = ZoomableImageView()
        self.canvas_stack.addWidget(self.preview_view)

        canvas_layout.addWidget(self.canvas_stack, 1)
        center.addWidget(self.canvas, 1)

        # Bottom zoom bar
        self.zoom_bar = ZoomBar()
        self.zoom_bar.fitRequested.connect(self.preview_view.reset_view)
        self.zoom_bar.compareRequested.connect(self._open_compare)
        self.zoom_bar.zoomChanged.connect(self._apply_zoom)
        center.addWidget(self.zoom_bar, 0)

        root.addLayout(center, 1)

        # === RIGHT: stacked edit panel / compressor panel ===
        self.edit_panel = EditPanel()
        self.edit_panel.paramsChanged.connect(self._on_params_changed)
        self.edit_panel.applyRequested.connect(self._apply_to_current)
        self.edit_panel.saveRequested.connect(self._action_save_as)
        self.edit_panel.resetRequested.connect(self._action_reset)
        self.edit_panel.rotateRequested.connect(self._rotate)
        self.edit_panel.flipRequested.connect(self._flip)
        self.edit_panel.saveCurrentRequested.connect(self._save_current)
        self.edit_panel.saveAsRequested.connect(self._save_as)
        self.edit_panel.batchExportRequested.connect(self._open_batch)
        self.edit_panel.tabChanged.connect(self._on_panel_tab_changed)

        self.compressor_panel = CompressorPanel()
        self.compressor_panel.estimateRequested.connect(self._compress_estimate)
        self.compressor_panel.previewRequested.connect(self._compress_preview)
        self.compressor_panel.saveCurrentRequested.connect(self._compress_save_current)
        self.compressor_panel.batchRequested.connect(self._compress_batch_run)
        self.compressor_panel.cancelBatchRequested.connect(self._compress_batch_cancel)

        self.right_stack = QStackedWidget()
        self.right_stack.addWidget(self.edit_panel)  # 0
        self.right_stack.addWidget(self.compressor_panel)  # 1
        root.addWidget(self.right_stack, 0)

        self.setStatusBar(QStatusBar())

    def _build_menu(self) -> None:
        mb = self.menuBar()
        file_menu = mb.addMenu("&File")
        self._add_action(file_menu, "Open Image…", self._action_open, "Ctrl+O")
        self._recent_menu = file_menu.addMenu("Open Recent")
        self._rebuild_recent_menu()
        file_menu.addSeparator()
        self._add_action(file_menu, "Save", self._save_current_quick, "Ctrl+S")
        self._add_action(file_menu, "Save As…", self._action_save_as, "Ctrl+Shift+S")
        self._add_action(file_menu, "Export…", self._action_export_dialog, "Ctrl+E")
        self._add_action(file_menu, "Batch Process…", self._open_batch, "Ctrl+B")
        file_menu.addSeparator()
        self._add_action(file_menu, "Quit", self.close, "Ctrl+Q")

        edit_menu = mb.addMenu("&Edit")
        self._add_action(edit_menu, "Undo", self._undo, "Ctrl+Z")
        self._add_action(edit_menu, "Redo", self._redo, "Ctrl+Y")
        self._add_action(edit_menu, "Reset All", self._action_reset, "Ctrl+R")

        view_menu = mb.addMenu("&View")
        self._add_action(view_menu, "Fit", self.preview_view.reset_view, "Ctrl+0")
        self._add_action(view_menu, "Actual Size (100%)", lambda: self._apply_zoom(1.0), "Ctrl+1")
        self._add_action(view_menu, "Compare Before / After", self._open_compare, "Ctrl+/")

        help_menu = mb.addMenu("&Help")
        self._add_action(help_menu, "Keyboard Shortcuts", self._show_shortcuts)
        self._add_action(help_menu, "About Vibrance", self._about)

    def _add_action(self, menu, label: str, slot, shortcut: str | None = None) -> QAction:
        a = QAction(label, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(slot)
        menu.addAction(a)
        return a

    def _wire_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._apply_to_current)

    # ----- recent files -----------------------------------------------
    def _load_recent(self) -> list[str]:
        raw = self._settings.value("recent_files", [], type=list)
        return [str(p) for p in (raw or []) if Path(p).is_file()]

    def _save_recent(self) -> None:
        self._settings.setValue("recent_files", self._recent)

    def _push_recent(self, path: str) -> None:
        if path in self._recent:
            self._recent.remove(path)
        self._recent.insert(0, path)
        self._recent = self._recent[: self.RECENT_LIMIT]
        self._save_recent()
        self._rebuild_recent_menu()

    def _rebuild_recent_menu(self) -> None:
        self._recent_menu.clear()
        if not self._recent:
            empty = QAction("(no recent files)", self)
            empty.setEnabled(False)
            self._recent_menu.addAction(empty)
            return
        for p in self._recent:
            act = QAction(Path(p).name, self)
            act.setToolTip(p)
            act.triggered.connect(lambda _c=False, path=p: self._open_path(path))
            self._recent_menu.addAction(act)
        self._recent_menu.addSeparator()
        clear = QAction("Clear", self)
        clear.triggered.connect(self._clear_recent)
        self._recent_menu.addAction(clear)

    def _clear_recent(self) -> None:
        self._recent.clear()
        self._save_recent()
        self._rebuild_recent_menu()

    # ----- tool rail handler ------------------------------------------
    def _on_tool_changed(self, tool: str) -> None:
        # Tools that stay in the editor view (tabs)
        if tool in ("adjust", "filters", "export"):
            self.right_stack.setCurrentIndex(0)
            if tool == "adjust":
                self.edit_panel.goto_tab(0)
            elif tool == "filters":
                self.edit_panel.goto_tab(1)
            else:  # export
                self.edit_panel.goto_tab(3)
            return

        # Compressor opens its dedicated panel
        if tool == "compressor":
            self.right_stack.setCurrentIndex(1)
            return

        # Action-style tools — execute and snap back to editor
        if tool == "open":
            self._action_open()
        elif tool == "crop":
            self._crop_current()
        elif tool == "batch":
            self._open_batch()
        elif tool == "compare":
            self._open_compare()
        elif tool == "help":
            self._show_shortcuts()
        # Return to the editor view + the previous editor tab
        self.right_stack.setCurrentIndex(0)
        self.tool_rail.select("adjust")

    def _on_panel_tab_changed(self, index: int) -> None:
        # Keep tool-rail selection in sync with relevant tabs
        if index == 0:
            self.tool_rail.select("adjust")
        elif index == 1:
            self.tool_rail.select("filters")
        elif index == 3:
            self.tool_rail.select("export")

    # ----- image lifecycle --------------------------------------------
    def _action_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open image",
            "",
            "Images (*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff)",
        )
        if path:
            self._open_path(path)

    def _open_path(self, path: str) -> None:
        try:
            img = load_image(path)
        except Exception as e:
            show_toast(self, f"Could not open: {e}", kind="error")
            self.log.error("open failed %s: %s", path, e)
            return
        self._current_image = img
        self._current_path = path
        self.history.reset()
        self.edit_panel.set_params(EditParams())
        self.canvas_stack.setCurrentIndex(1)  # show preview
        self._render_preview(force=True)
        self._thumb_timer.start(self.THUMB_DEBOUNCE_MS)
        self._push_recent(path)
        show_toast(self, f"Loaded {Path(path).name}", kind="info", duration_ms=1800)
        self.statusBar().showMessage(f"{Path(path).name}  ·  {img.shape[1]}×{img.shape[0]}")

    def _on_params_changed(self, _p: EditParams) -> None:
        self._preview_timer.start(self.PREVIEW_DEBOUNCE_MS)

    def _render_preview(self, force: bool = False) -> None:
        if self._current_image is None:
            return
        params = self.edit_panel.params()
        try:
            self._preview_image = process(self._current_image, params)
        except Exception as e:
            self.log.exception("preview failed: %s", e)
            self._preview_image = self._current_image
        self.preview_view.set_image(_bgr_to_pixmap(self._preview_image))
        if not force:
            self.history.push(params)

    def _refresh_thumbnails(self) -> None:
        if self._current_image is not None:
            self.edit_panel.set_source_image(self._current_image)

    # ----- undo / redo / reset ----------------------------------------
    def _undo(self) -> None:
        self.edit_panel.set_params(self.history.undo())

    def _redo(self) -> None:
        self.edit_panel.set_params(self.history.redo())

    def _action_reset(self) -> None:
        self.edit_panel.set_params(EditParams())

    # ----- geometry ----------------------------------------------------
    def _rotate(self, delta_deg: int) -> None:
        if self._current_image is None:
            return
        if delta_deg == 90:
            self._current_image = cv2.rotate(self._current_image, cv2.ROTATE_90_CLOCKWISE)
        elif delta_deg == -90:
            self._current_image = cv2.rotate(self._current_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        self._render_preview(force=True)
        self._thumb_timer.start(self.THUMB_DEBOUNCE_MS)

    def _flip(self, axis: str) -> None:
        if self._current_image is None:
            return
        self._current_image = cv2.flip(self._current_image, 1 if axis == "h" else 0)
        self._render_preview(force=True)
        self._thumb_timer.start(self.THUMB_DEBOUNCE_MS)

    # ----- crop --------------------------------------------------------
    def _crop_current(self) -> None:
        if self._current_image is None:
            show_toast(self, "Open an image first.", kind="error")
            return
        dlg = CropDialog(_bgr_to_pixmap(self._current_image), self)
        if dlg.exec() != dlg.Accepted:
            return
        rect = dlg.result_rect()
        if not rect:
            return
        x, y, w, h = rect
        self._current_image = self._current_image[y : y + h, x : x + w].copy()
        self._render_preview(force=True)
        self._thumb_timer.start(self.THUMB_DEBOUNCE_MS)

    # ----- apply / save -----------------------------------------------
    def _apply_to_current(self) -> None:
        """Bake current edit params into the source image so further edits
        stack on top of the rendered result."""
        if self._preview_image is None:
            show_toast(self, "Open an image first.", kind="error")
            return
        self._current_image = self._preview_image.copy()
        self.edit_panel.set_params(EditParams())
        self.history.reset()
        show_toast(self, "Edits applied to source.", duration_ms=1500)

    def _action_save_as(self) -> None:
        if self._preview_image is None:
            show_toast(self, "Nothing to save.", kind="error")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save image as",
            self._suggest_name("jpg"),
            "JPEG (*.jpg);;PNG (*.png);;WebP (*.webp);;TIFF (*.tif)",
        )
        if not path:
            return
        try:
            save_compressed(path, self._preview_image, quality=92)
            show_toast(self, f"Saved → {Path(path).name}")
        except Exception as e:
            show_toast(self, f"Save failed: {e}", kind="error")

    def _save_current(self, settings) -> None:
        if self._preview_image is None:
            show_toast(self, "Nothing to save.", kind="error")
            return
        if not self._current_path:
            return self._save_as(settings)
        path = self._suggest_name(settings.fmt)
        self._do_save(path, settings)

    def _save_as(self, settings) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save image as",
            self._suggest_name(settings.fmt),
            f"{settings.fmt.upper()} (*.{settings.fmt})",
        )
        if path:
            self._do_save(path, settings)

    def _save_current_quick(self) -> None:
        if self._preview_image is None or not self._current_path:
            return self._action_save_as()
        path = self._suggest_name("jpg")
        try:
            save_compressed(path, self._preview_image, quality=92)
            show_toast(self, f"Saved → {Path(path).name}")
        except Exception as e:
            show_toast(self, f"Save failed: {e}", kind="error")

    def _action_export_dialog(self) -> None:
        self.edit_panel.goto_tab(3)
        show_toast(self, "Configure export settings, then click Save / Save As.", duration_ms=2200)

    def _do_save(self, path: str, settings) -> None:
        try:
            img = self._preview_image
            if settings.resize_width > 0 or settings.resize_height > 0:
                w, h = settings.resize_width, settings.resize_height
                long_edge = max(w, h) if w and h else (w or h)
                img = resize_long_edge(img, long_edge)
            save_compressed(path, img, quality=settings.quality, fmt=settings.fmt)
            if settings.strip_metadata:
                strip_metadata(path)
            show_toast(self, f"Exported → {Path(path).name}")
        except Exception as e:
            show_toast(self, f"Export failed: {e}", kind="error")

    def _suggest_name(self, fmt: str) -> str:
        if not self._current_path:
            return f"export.{fmt}"
        stem = Path(self._current_path).stem
        parent = Path(self._current_path).parent
        return str(parent / f"{stem}_vibrance.{fmt}")

    # ----- batch ------------------------------------------------------
    def _open_batch(self, _settings=None) -> None:
        params = self.edit_panel.params()
        self._batch_dialog = BatchDialog(params, self)
        self._batch_dialog.runRequested.connect(self._run_batch)
        self._batch_dialog.cancelRequested.connect(self._cancel_batch)
        self._batch_dialog.show()

    def _run_batch(self, opts: dict) -> None:
        files = opts["files"]
        out_dir = opts["out_dir"] or str(Path(files[0]).parent / OUTPUT_SUBDIR)
        export_fmt = opts["fmt"] if opts["fmt"] != "(keep original)" else ""
        params = opts["params"]
        export_opts = ExportOptions(
            format=export_fmt or "jpg",
            quality=opts["quality"],
            resize_long_edge=opts["long_edge"],
            output_dir=out_dir,
            suffix="_vibrance",
        )
        self._worker = BatchEditWorker(files, params, export_opts)
        self._worker.progress.connect(self._on_batch_progress)
        self._worker.finished.connect(self._on_batch_finished)
        self._ok_count = 0
        self._fail_count = 0
        self._worker.fileDone.connect(lambda *_: self._inc_ok())
        self._worker.error.connect(lambda *_: self._inc_fail())
        self._worker.start()

    def _inc_ok(self) -> None:
        self._ok_count += 1

    def _inc_fail(self) -> None:
        self._fail_count += 1

    def _on_batch_progress(self, pct: int) -> None:
        if self._batch_dialog is not None:
            self._batch_dialog.set_progress(pct)

    def _on_batch_finished(self) -> None:
        if self._batch_dialog is not None:
            self._batch_dialog.finished(self._ok_count, self._fail_count)
        show_toast(
            self,
            f"Batch done: {self._ok_count} ok, {self._fail_count} failed",
            kind="error" if self._fail_count else "info",
        )
        self._worker = None

    def _cancel_batch(self) -> None:
        if self._worker is not None:
            self._worker.cancel()

    # ----- compressor handlers ----------------------------------------
    def _compress_estimate(self, req) -> None:
        """Encode the current preview at the requested settings in-memory and
        report the resulting file size without writing to disk."""
        if self._preview_image is None:
            show_toast(self, "Open an image first.", kind="error")
            return
        from image_editor.core.compress import compress_quality, compress_to_size

        try:
            img = self._resize_for_compress(self._preview_image, req)
            if req.target_kb > 0:
                r = compress_to_size(img, target_kb=req.target_kb, fmt=req.fmt)
            else:
                r = compress_quality(img, fmt=req.fmt, quality=req.quality)
            src_kb = Path(self._current_path).stat().st_size / 1024.0 if self._current_path else 0.0
            text = f"Estimated: {r.size_kb:.1f} KB · q={r.quality_used} · {r.width}×{r.height}"
            if src_kb > 0:
                pct = max(0.0, (1 - r.size_kb / src_kb) * 100)
                text += f"  ·  saves {pct:.0f}%"
            self.compressor_panel.set_single_result(text)
        except Exception as e:
            show_toast(self, f"Estimate failed: {e}", kind="error")

    def _compress_preview(self, req) -> None:
        """Compute the compressed bytes and load them back into the canvas so
        the user can see exactly what they'll get."""
        if self._preview_image is None:
            show_toast(self, "Open an image first.", kind="error")
            return
        import cv2
        import numpy as np

        from image_editor.core.compress import compress_quality, compress_to_size

        try:
            img = self._resize_for_compress(self._preview_image, req)
            if req.target_kb > 0:
                r = compress_to_size(img, target_kb=req.target_kb, fmt=req.fmt)
            else:
                r = compress_quality(img, fmt=req.fmt, quality=req.quality)
            arr = np.frombuffer(r.bytes_out, dtype=np.uint8)
            decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if decoded is None:
                raise ValueError("could not decode compressed preview")
            self._preview_image = decoded
            self.preview_view.set_image(_bgr_to_pixmap(decoded))
            self.compressor_panel.set_single_result(
                f"Preview: {r.size_kb:.1f} KB · q={r.quality_used}"
            )
        except Exception as e:
            show_toast(self, f"Preview failed: {e}", kind="error")

    def _compress_save_current(self, req) -> None:
        """Save the compressed image to a user-chosen path. Originals are
        never overwritten silently — the dialog defaults to a *_vibrance name."""
        if self._preview_image is None:
            show_toast(self, "Open an image first.", kind="error")
            return
        suggested = self._suggest_name(req.fmt)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save compressed image",
            suggested,
            f"{req.fmt.upper()} (*.{req.fmt})",
        )
        if not path:
            return
        # Refuse silent overwrite of the source file
        if self._current_path and Path(path).resolve() == Path(self._current_path).resolve():
            box = QMessageBox.question(
                self,
                "Overwrite original?",
                "This will overwrite your original file. Continue?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if box != QMessageBox.Yes:
                return
        from image_editor.core.compress import save_compressed

        try:
            img = self._resize_for_compress(self._preview_image, req)
            target = req.target_kb if req.target_kb > 0 else None
            r = save_compressed(path, img, target_kb=target, quality=req.quality, fmt=req.fmt)
            if req.strip_metadata:
                strip_metadata(path)
            src_kb = Path(self._current_path).stat().st_size / 1024.0 if self._current_path else 0.0
            text = f"Saved {Path(path).name}  ·  {r.size_kb:.1f} KB" + (
                f"  ·  {(1 - r.size_kb / src_kb) * 100:.0f}% smaller" if src_kb > 0 else ""
            )
            self.compressor_panel.set_single_result(text)
            show_toast(self, text)
        except Exception as e:
            show_toast(self, f"Compress failed: {e}", kind="error")

    @staticmethod
    def _resize_for_compress(img, req):
        long_edge = max(req.resize_width, req.resize_height)
        return resize_long_edge(img, long_edge) if long_edge > 0 else img

    def _compress_batch_run(self, req) -> None:
        if not req.in_dir or not Path(req.in_dir).is_dir():
            show_toast(self, "Pick an input folder first.", kind="error")
            self.compressor_panel.set_batch_summary("Pick a valid input folder.")
            return
        files = [
            str(p)
            for p in Path(req.in_dir).iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
        ]
        if not files:
            show_toast(self, "No supported images found in folder.", kind="error")
            self.compressor_panel.set_batch_summary("No images found.")
            return
        out_dir = req.out_dir or str(Path(req.in_dir) / "compressed")
        if Path(out_dir).resolve() == Path(req.in_dir).resolve():
            box = QMessageBox.question(
                self,
                "Same folder?",
                "Output folder is the same as input. Continue (files are renamed)?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if box != QMessageBox.Yes:
                return

        self._compress_worker = BatchCompressWorker(
            files=files,
            out_dir=out_dir,
            fmt=req.fmt,
            quality=req.quality,
            target_kb=req.target_kb,
            long_edge=req.long_edge,
            strip_meta=req.strip_metadata,
        )
        self._compress_worker.progress.connect(self.compressor_panel.set_batch_progress)
        self._compress_worker.finishedSummary.connect(self._on_compress_batch_done)
        self._compress_worker.start()

    def _on_compress_batch_done(self, ok: int, fail: int, saved_kb: float) -> None:
        summary = (
            f"Done · {ok} succeeded · {fail} failed" f"  ·  saved {saved_kb / 1024:.1f} MB total"
        )
        self.compressor_panel.set_batch_summary(summary)
        show_toast(self, summary, kind="error" if fail else "info")
        self._compress_worker = None

    def _compress_batch_cancel(self) -> None:
        if getattr(self, "_compress_worker", None) is not None:
            self._compress_worker.cancel()
            self.compressor_panel.set_batch_summary("Cancelled.")

    # ----- compare ----------------------------------------------------
    def _open_compare(self) -> None:
        if self._current_image is None or self._preview_image is None:
            show_toast(self, "Open an image with some edits first.", kind="error")
            return
        self._compare_window = SplitCompareWidget(
            _bgr_to_pixmap(self._current_image),
            _bgr_to_pixmap(self._preview_image),
        )
        self._compare_window.setWindowTitle("Compare — Before / After")
        self._compare_window.resize(1100, 700)
        self._compare_window.show()

    # ----- zoom -------------------------------------------------------
    def _apply_zoom(self, zoom: float) -> None:
        self.preview_view.resetTransform()
        self.preview_view.scale(zoom, zoom)
        self.preview_view._scale = zoom  # noqa: SLF001

    # ----- help -------------------------------------------------------
    def _show_shortcuts(self) -> None:
        QMessageBox.information(
            self,
            "Keyboard Shortcuts",
            "<b>File</b><br/>"
            "Ctrl+O — Open<br/>"
            "Ctrl+S — Save<br/>"
            "Ctrl+Shift+S — Save As<br/>"
            "Ctrl+E — Export tab<br/>"
            "Ctrl+B — Batch<br/>"
            "<br/><b>Edit</b><br/>"
            "Ctrl+Z — Undo<br/>"
            "Ctrl+Y — Redo<br/>"
            "Ctrl+R — Reset all<br/>"
            "Ctrl+Enter — Apply edits<br/>"
            "<br/><b>View</b><br/>"
            "Ctrl+0 — Fit<br/>"
            "Ctrl+1 — Actual size<br/>"
            "Ctrl+/ — Compare before/after",
        )

    def _about(self) -> None:
        from image_editor import __version__

        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h3>{APP_NAME}</h3>"
            f"<p>Version {__version__}  ·  fully offline</p>"
            "<p>Photo editor, batch processor, compressor.<br/>"
            "Built with PySide6 + OpenCV.</p>"
            "<p>© Sandeep Bollavaram · MIT License</p>",
        )

    # ----- drag & drop on the whole window -----------------------------
    def dragEnterEvent(self, e):  # noqa: N802
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):  # noqa: N802
        for u in e.mimeData().urls():
            p = Path(u.toLocalFile())
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                self._open_path(str(p))
                return
        show_toast(self, "Unsupported file type.", kind="error")
