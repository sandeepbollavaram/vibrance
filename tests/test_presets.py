import image_editor.core.presets as presets_mod
from image_editor.config import EditParams


def test_preset_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(presets_mod, "user_data_dir", lambda: tmp_path)
    p = EditParams(brightness=33, vibrance=12, lut_path="x.cube")
    presets_mod.save_preset("demo", p)
    assert "demo" in presets_mod.list_presets()
    back = presets_mod.load_preset("demo")
    assert back.brightness == 33
    assert back.vibrance == 12
    assert back.lut_path == "x.cube"
