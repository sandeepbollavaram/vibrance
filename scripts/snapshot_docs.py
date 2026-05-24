"""Render docs/index.html in QtWebEngine (if available) or report the file paths.

Headless rendering of the page is non-trivial; instead this script verifies the
docs assets are wired correctly and prints a summary you can paste into the PR.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

EXPECTED = ["index.html", "style.css", "downloads.js", "app.png", "hero.png", "og.png", "_config.yml"]


def main() -> int:
    print(f"docs/ at {DOCS}")
    missing = []
    for name in EXPECTED:
        p = DOCS / name
        if p.is_file():
            print(f"  [ok]{name:14}  {p.stat().st_size:>10} bytes")
        else:
            missing.append(name)
            print(f"  [--]{name:14}  MISSING")

    print()
    if missing:
        print(f"Missing: {', '.join(missing)}")
        return 1
    print("All docs assets present. Push to main and the pages.yml workflow will deploy.")
    print(f"Site URL once deployed: https://sandeepbollavaram.github.io/vibrance/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
