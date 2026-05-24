from image_editor.config import EditParams
from image_editor.core.history import History


def test_push_and_undo_redo():
    h = History()
    assert not h.can_undo()
    h.push(EditParams(brightness=10))
    h.push(EditParams(brightness=20))
    assert h.current.brightness == 20
    assert h.can_undo()
    h.undo()
    assert h.current.brightness == 10
    h.redo()
    assert h.current.brightness == 20


def test_duplicate_push_is_noop():
    h = History()
    h.push(EditParams(brightness=10))
    h.push(EditParams(brightness=10))
    h.undo()
    assert h.current == EditParams()


def test_redo_branch_truncated_on_new_push():
    h = History()
    h.push(EditParams(brightness=10))
    h.push(EditParams(brightness=20))
    h.undo()
    h.push(EditParams(brightness=99))
    assert not h.can_redo()
    assert h.current.brightness == 99
