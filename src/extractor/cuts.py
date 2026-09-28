from __future__ import annotations
from .selectors import CUT_TOKEN_RE


def split_cuts(inner: str) -> tuple[str, list[dict[str, str]]]:
    """
    Делит inner-HTML на visible_html и список cut-блоков.

    На месте cut-блока в visible_html остаётся маркер <cut id="cutidN" />.
    Содержимое блока (без хвоста </a> от якоря) уходит в cuts.
    """
    tokens: list[tuple] = []
    pos = 0
    for m in CUT_TOKEN_RE.finditer(inner):
        if m.start() > pos:
            tokens.append(("text", inner[pos:m.start()]))
        kind = "end" if m.group(2) else "start"
        tokens.append((kind, m.group(1)))
        pos = m.end()
    if pos < len(inner):
        tokens.append(("text", inner[pos:]))

    visible_parts: list[str] = []
    cuts: list[dict[str, str]] = []
    mode = "visible"
    cur_id: str | None = None
    cur_buf: list[str] = []

    for tok in tokens:
        kind = tok[0]
        if kind == "text":
            (visible_parts if mode == "visible" else cur_buf).append(tok[1])
        elif kind == "start":
            if mode == "cut":
                cuts.append({"id": cur_id or "?", "html": "".join(cur_buf).strip()})
                cur_buf = []
            mode, cur_id = "cut", tok[1]
            visible_parts.append(f'<cut id="{tok[1]}" />')
        elif kind == "end":
            if mode == "cut":
                cuts.append({"id": cur_id or "?", "html": "".join(cur_buf).strip()})
                cur_buf, cur_id, mode = [], None, "visible"
            # закрывающий якорь отбрасываем — уже представлен маркером

    if mode == "cut":
        cuts.append({"id": cur_id or "?", "html": "".join(cur_buf).strip()})

    return "".join(visible_parts).strip(), cuts