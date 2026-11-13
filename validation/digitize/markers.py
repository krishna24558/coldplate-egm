"""Find filled plot markers (squares, diamonds, triangles) in a scanned figure,
including markers that overlap or hide behind each other.

Method (matching pursuit with binary templates):
  1. Templates are built from clean, isolated markers in the same figure (the
     mean of their binary masks), so size and stroke match the scan.
  2. For every template and position, a score is computed:
        coverage  = fraction of template pixels that are ink
        spill     = fraction of a 2-px ring around the template that is ink,
                    ignoring pixels already explained by accepted markers
     score = coverage - spill.
  3. The best candidate is accepted, its pixels are marked as explained, and
     the scores are recomputed. Later candidates (partly hidden markers) must add
     at least `min_new` unexplained ink pixels. Stops when no candidate passes.
Reported position = area centroid of the template placed at the match (the same
definition as WebPlotDigitizer's blob detector). Pixel positions are converted
to data by WebPlotDigitizer's calibration (wpd_run.js, "manual" dataset).
"""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi
from scipy.signal import fftconvolve


@dataclass
class Marker:
    shape: str
    row: float      # area-centroid row (px)
    col: float      # area-centroid column (px)
    coverage: float
    spill: float
    new_px: int     # ink pixels this marker explained when accepted
    hidden: bool    # True if most of it was already ink of other markers


def classify_component(mask: np.ndarray) -> str:
    """Rough shape class of one isolated binary marker."""
    h, w = mask.shape
    fill = mask.sum() / (h * w)
    rows = np.nonzero(mask)[0]
    skew = (rows.mean() - (h - 1) / 2) / h  # >0: mass low -> apex up
    if fill > 0.85:
        return "square"
    if abs(h - w) <= 3 and abs(skew) < 0.04:
        return "diamond"
    return "tri_up" if skew > 0 else "tri_down"


def build_templates(ink: np.ndarray, size_range=(12, 40), exclude=()) -> dict:
    """Average the masks of isolated, clean markers of each class."""
    lab, n = ndi.label(ink, structure=np.ones((3, 3)))
    groups = {}
    for i, sl in enumerate(ndi.find_objects(lab), start=1):
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if not (size_range[0] <= h <= size_range[1] and size_range[0] <= w <= size_range[1]):
            continue
        if any(r0 <= sl[0].start <= r1 and c0 <= sl[1].start <= c1 for r0, c0, r1, c1 in exclude):
            continue
        m = lab[sl] == i
        groups.setdefault((classify_component(m), h, w), []).append(m)
    templates = {}
    for shape in ("square", "diamond", "tri_up", "tri_down"):
        cands = [(len(v), k) for k, v in groups.items() if k[0] == shape]
        if not cands:
            continue
        _, key = max(cands)               # most common size for this shape
        stack = np.mean([g.astype(float) for g in groups[key]], axis=0)
        templates[shape] = {"mask": stack >= 0.5, "n_examples": len(groups[key])}
    return templates


def _ring(mask: np.ndarray, gap: int = 1, width: int = 2) -> np.ndarray:
    """Ring of `width` px starting `gap` px outside the template (gap tolerates
    1-px size differences between instances)."""
    pad = np.pad(mask, gap + width)
    inner = ndi.binary_dilation(pad, iterations=gap)
    return ndi.binary_dilation(pad, iterations=gap + width) & ~inner


def find_markers(ink: np.ndarray, templates: dict, min_cov: float = 0.93,
                 max_spill: float = 0.15, min_new: int = 40, max_iter: int = 2000,
                 shapes=None) -> list:
    """Matching pursuit over all templates; returns accepted markers."""
    shapes = shapes or list(templates)
    inkf = ink.astype(float)
    explained = np.zeros_like(ink, dtype=bool)
    pre = {}
    for s in shapes:
        t = templates[s]["mask"]
        ring = _ring(t)
        tp = np.pad(t, 3)
        pre[s] = {"t": tp, "ring": ring, "nt": tp.sum(), "nr": ring.sum(),
                  "cov": fftconvolve(inkf, tp[::-1, ::-1].astype(float), mode="same") / tp.sum()}
    out = []
    for _ in range(max_iter):
        unexpl = (ink & ~explained).astype(float)
        best = None
        for s in shapes:
            P = pre[s]
            spill_ink = fftconvolve((ink & ~explained).astype(float), P["ring"][::-1, ::-1].astype(float),
                                    mode="same") / P["nr"]
            new = fftconvolve(unexpl, P["t"][::-1, ::-1].astype(float), mode="same")
            score = P["cov"] - spill_ink
            ok = (P["cov"] >= min_cov) & (spill_ink <= max_spill) & (new >= min_new)
            if not ok.any():
                continue
            sc = np.where(ok, score + 1e-4 * new, -np.inf)
            idx = np.unravel_index(np.argmax(sc), sc.shape)
            if best is None or sc[idx] > best[0]:
                best = (sc[idx], s, idx, P["cov"][idx], spill_ink[idx], new[idx])
        if best is None:
            break
        _, s, (r, c), cov, sp, nnew = best
        t = pre[s]["t"]
        h, w = t.shape
        r0, c0 = r - h // 2, c - w // 2
        rr, cc = np.nonzero(t)
        rr = rr + r0
        cc = cc + c0
        keep = (rr >= 0) & (rr < ink.shape[0]) & (cc >= 0) & (cc < ink.shape[1])
        explained[rr[keep], cc[keep]] = True
        out.append(Marker(s, float(rr.mean() + 0.5), float(cc.mean() + 0.5), float(cov),
                          float(sp), int(nnew), bool(nnew < 0.6 * pre[s]["nt"])))
    leftover = ink & ~explained
    return out, leftover


def dedupe(markers: list, dx: float = 12.0, dy: float = 4.0) -> list:
    """Merge same-shape detections closer than (dx, dy) px: a partly hidden marker
    is offset mainly vertically (repeat runs at nearly the same Re), while side-by-
    side copies at the same height are fitting artefacts. Keeps the one that
    explained most pixels."""
    kept = []
    for m in sorted(markers, key=lambda m: -m.new_px):
        if any(k.shape == m.shape and abs(k.col - m.col) < dx and abs(k.row - m.row) < dy
               for k in kept):
            continue
        kept.append(m)
    return kept
