"""Все константы и регэкспы. Править тут при изменении вёрстки ЖЖ."""
from __future__ import annotations
import re

# --- формат вёрстки ---
NEW_ARTICLE_CLASS_RE = re.compile(r"\bb-singlepost-body\b")

# --- видимость поста ---
VISIBILITY_CLASSES = {
    "i-posticon-public":   "public",
    "i-posticon-private":  "private",
    "i-posticon-friends":  "friends",
}
VISIBILITY_IMG_RE = re.compile(r"icon_(public|private|friends)", re.I)

# --- регэкспы ---
# Якорь ката матчится целиком вместе с закрывающим </a> — иначе его хвост
# оставался в содержимом ката.
CUT_TOKEN_RE = re.compile(
    r'<a\s+name=["\']?(cutid\d+)(-end)?["\']?[^>]*>'
    r'(?:\s*</a\s*>)?',
    re.I,
)

ISO_RE = re.compile(
    r"(\d{4})\s*-\s*(\d{2})\s*-\s*(\d{2})"
    r"(?:[ T]+(\d{1,2}):(\d{2})(?::(\d{2}))?)?"
)
YMD_PATH_RE = re.compile(r"/(\d{4})/(\d{2})/(\d{2})/?$")
YM_PATH_RE  = re.compile(r"/(\d{4})/(\d{2})/?$")
Y_PATH_RE   = re.compile(r"/(\d{4})/?$")
TIME_IN_TEXT_RE = re.compile(r"(\d{1,2}):(\d{2})(?::(\d{2}))?")