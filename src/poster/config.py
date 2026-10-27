"""Конфиг poster. По возможности переиспользует generator.config."""
from __future__ import annotations
import sys
from pathlib import Path

# Гарантируем, что src/ есть в sys.path — чтобы `import generator.config`
# работал независимо от cwd.
_HERE = Path(__file__).resolve()
_SRC = _HERE.parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

try:
    from generator.config import (  # type: ignore
        JSON_DIR as _DEFAULT_JSON_DIR,
        STATIC_DIR as _GEN_STATIC_DIR,
        MOOD_ICONS_DIR as _MOOD_ICONS_DIR,
    )
except Exception:
    _DEFAULT_JSON_DIR = (_SRC.parent / "json").resolve()
    _GEN_STATIC_DIR = _SRC / "generator" / "static"
    _MOOD_ICONS_DIR = "img/mood"

JSON_DIR = Path(_DEFAULT_JSON_DIR).resolve()
GENERATOR_STATIC_DIR = Path(_GEN_STATIC_DIR).resolve()
MOOD_DIR = (GENERATOR_STATIC_DIR / _MOOD_ICONS_DIR).resolve()
STYLESHEET = GENERATOR_STATIC_DIR / "css" / "style.css"

UI_DIR = _HERE.parent / "ui"

# Значения по умолчанию для формы
DEFAULT_VISIBILITY = "public"
DEFAULT_EXPAND_TEXT = "читать далее..."
DEFAULT_CUT_ID = "cutid1"
POST_SUFFIX = ".json"
BACKUP_SUFFIX = ".bak"