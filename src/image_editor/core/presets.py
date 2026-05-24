from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path

from image_editor.config import PRESETS_DIR_NAME, EditParams, user_data_dir


def _presets_dir() -> Path:
    p = user_data_dir() / PRESETS_DIR_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_preset(name: str, params: EditParams) -> Path:
    name = name.strip() or "preset"
    safe = "".join(c for c in name if c.isalnum() or c in ("-", "_", " ")).strip().replace(" ", "_")
    path = _presets_dir() / f"{safe}.json"
    path.write_text(json.dumps(asdict(params), indent=2), encoding="utf-8")
    return path


def load_preset(name_or_path: str) -> EditParams:
    p = Path(name_or_path)
    if not p.is_file():
        p = _presets_dir() / f"{name_or_path}.json"
    raw = json.loads(p.read_text(encoding="utf-8"))
    valid = {f.name for f in fields(EditParams)}
    return EditParams(**{k: v for k, v in raw.items() if k in valid})


def list_presets() -> list[str]:
    return sorted(p.stem for p in _presets_dir().glob("*.json"))
