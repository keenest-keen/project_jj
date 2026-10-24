"""python -m poster.vendor — скачивает Quill в ui/vendor/quill/ (один раз)."""
from __future__ import annotations
import urllib.request
from pathlib import Path

QUILL_VERSION = "2.0.3"
BASE = f"https://cdn.jsdelivr.net/npm/quill@{QUILL_VERSION}/dist"
FILES = {
    "quill.js": f"{BASE}/quill.js",
    "quill.snow.css": f"{BASE}/quill.snow.css",
}


def main() -> None:
    dest = Path(__file__).parent / "ui" / "vendor" / "quill"
    dest.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        target = dest / name
        print(f"↓ {url}")
        print(f"  → {target}")
        with urllib.request.urlopen(url) as r, target.open("wb") as f:
            f.write(r.read())
    print("готово: Quill вендорён локально")


if __name__ == "__main__":
    main()