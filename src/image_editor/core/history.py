from __future__ import annotations

from dataclasses import replace

from image_editor.config import EditParams


class History:
    """Simple bounded undo/redo stack of EditParams snapshots."""

    def __init__(self, initial: EditParams | None = None, limit: int = 100):
        self._stack: list[EditParams] = [replace(initial or EditParams())]
        self._index: int = 0
        self._limit = limit

    @property
    def current(self) -> EditParams:
        return self._stack[self._index]

    def push(self, params: EditParams) -> None:
        snap = replace(params)
        if snap == self._stack[self._index]:
            return
        # truncate redo branch
        self._stack = self._stack[: self._index + 1]
        self._stack.append(snap)
        if len(self._stack) > self._limit:
            self._stack.pop(0)
        else:
            self._index += 1

    def can_undo(self) -> bool:
        return self._index > 0

    def can_redo(self) -> bool:
        return self._index < len(self._stack) - 1

    def undo(self) -> EditParams:
        if self.can_undo():
            self._index -= 1
        return self.current

    def redo(self) -> EditParams:
        if self.can_redo():
            self._index += 1
        return self.current

    def reset(self, params: EditParams | None = None) -> None:
        self._stack = [replace(params or EditParams())]
        self._index = 0
