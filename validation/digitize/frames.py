"""Locate a plot frame and its tick marks in a scanned figure (slight skew allowed)."""

import numpy as np


def _runs(v):
    d = np.diff(np.r_[0, v.astype(int), 0])
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))


def line_row(ink, col, r_lo, r_hi):
    """Centre row of the horizontal frame line crossing column `col` within [r_lo, r_hi]."""
    rr = [r for r in range(r_lo, r_hi) if ink[r, col]]
    if not rr:
        return None
    # longest contiguous group
    best, cur = [], []
    for r in rr:
        if cur and r != cur[-1] + 1:
            best = max(best, cur, key=len)
            cur = []
        cur.append(r)
    best = max(best, cur, key=len)
    return (best[0] + best[-1]) / 2


def line_col(ink, row, c_lo, c_hi):
    return line_row(ink.T, row, c_lo, c_hi)


def find_frame(ink, box, band=12):
    """box = approximate (top, bottom, left, right). Returns fitted lines:
    rows as functions of column (top/bottom) and columns as functions of row
    (left/right), each a (slope, intercept) least-squares fit."""
    T, B, L, R = box
    fits = {}
    cols = np.arange(L + 40, R - 40, 10)
    for name, r0 in (("top", T), ("bottom", B)):
        pts = [(c, line_row(ink, c, r0 - band, r0 + band)) for c in cols]
        pts = np.array([p for p in pts if p[1] is not None])
        fits[name] = np.polyfit(pts[:, 0], pts[:, 1], 1)
    rows = np.arange(T + 40, B - 40, 10)
    for name, c0 in (("left", L), ("right", R)):
        pts = [(r, line_col(ink, r, c0 - band, c0 + band)) for r in rows]
        pts = np.array([p for p in pts if p[1] is not None])
        fits[name] = np.polyfit(pts[:, 0], pts[:, 1], 1)
    return fits


def ticks(ink, fits, side="bottom", minlen=5, maxprobe=40, half=2):
    """Inward ticks on one frame side: list of (position along the axis, length).
    Position is a column for bottom/top and a row for left/right."""
    f = fits[side]
    if side in ("bottom", "top"):
        lo, hi = np.polyval(fits["left"], np.polyval(f, 0)), np.polyval(fits["right"], np.polyval(f, 0))
        sign = -1 if side == "bottom" else 1
        pos = np.arange(int(lo) + 6, int(hi) - 5)
        lens = []
        for c in pos:
            r = int(round(np.polyval(f, c))) + sign * (half + 1)
            n = 0
            while n < maxprobe and ink[r + sign * n, c]:
                n += 1
            lens.append(n)
    else:
        lo, hi = np.polyval(fits["top"], np.polyval(f, 0)), np.polyval(fits["bottom"], np.polyval(f, 0))
        sign = 1 if side == "left" else -1
        pos = np.arange(int(lo) + 6, int(hi) - 5)
        lens = []
        for r in pos:
            c = int(round(np.polyval(f, r))) + sign * (half + 1)
            n = 0
            while n < maxprobe and ink[r, c + sign * n]:
                n += 1
            lens.append(n)
    lens = np.array(lens)
    out = []
    on = lens >= minlen
    for a, b in _runs(on):
        out.append(((pos[a] + pos[b - 1]) / 2.0, int(lens[a:b].max())))
    return out


def point_on(fits, side, pos):
    """(col, row) of the frame line `side` at axis position `pos`."""
    if side in ("bottom", "top"):
        return float(pos), float(np.polyval(fits[side], pos))
    return float(np.polyval(fits[side], pos)), float(pos)
