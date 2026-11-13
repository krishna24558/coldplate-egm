// Headless WebPlotDigitizer runner.
//
// Runs WebPlotDigitizer's own calibration (wpd.XYAxes), colour thresholding
// (wpd.AutoDetectionData) and marker detection (wpd.BlobDetectorAlgo) on a plot
// image, i.e. the same steps as the browser app's "2D (X-Y) Plot -> Automatic
// extraction -> Blob detector" workflow, without the UI. The WPD source files are
// vendored unmodified in wpd_core/ (AGPL-3.0, commit in wpd_core/SOURCE_COMMIT.txt).
//
// Usage: node wpd_run.js config.json
// config = {
//   "rgba": "image.rgba", "width": W, "height": H,          // raw RGBA bytes (written by digitize.py)
//   "calibration": {"x1": [px, py, value], "x2": [...], "y1": [...], "y2": [...],
//                   "logX": false, "logY": false},
//   "datasets": [{"name": "...", "mask": [[x0, y0, x1, y1], ...],   // pixel rectangles to search
//                 "exclude": [[x0, y0, x1, y1], ...],               // optional
//                 "fgColor": [0, 0, 0], "colorDistance": 120,
//                 "minDia": 3, "maxDia": 20,
//                 "manual": [[px, py], ...]}],                     // optional: picked points instead
//   "out": "result.json"
// }
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const core = path.join(__dirname, "wpd_core");
const files = ["mathFunctions.js", "color.js", "inputParser.js", "dateConversion.js", "calibration.js",
    "xy.js", "map.js", "dataset.js", "rle.js", "autoDetection.js", "blobdetector.js"];
const ctx = {console, Math, Set, Array, Object, Number, parseFloat, parseInt, isNaN, Date};
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext("var wpd = {};", ctx);
for (const f of files) {
    vm.runInContext(fs.readFileSync(path.join(core, f), "utf8"), ctx, {filename: f});
}
const wpd = vm.runInContext("wpd", ctx);

const cfg = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const base = path.dirname(path.resolve(process.argv[2]));
const W = cfg.width, H = cfg.height;
const imageData = {data: new Uint8ClampedArray(fs.readFileSync(path.resolve(base, cfg.rgba))),
                   width: W, height: H};

const c = cfg.calibration;
const cal = new wpd.Calibration(2);
cal.addPoint(c.x1[0], c.x1[1], String(c.x1[2]), "0");
cal.addPoint(c.x2[0], c.x2[1], String(c.x2[2]), "0");
cal.addPoint(c.y1[0], c.y1[1], "0", String(c.y1[2]));
cal.addPoint(c.y2[0], c.y2[1], "0", String(c.y2[2]));
const axes = new wpd.XYAxes();
if (!axes.calibrate(cal, !!c.logX, !!c.logY, false)) {
    throw new Error("calibration failed");
}

function inRects(x, y, rects) {
    return (rects || []).some(r => x >= r[0] && x <= r[2] && y >= r[1] && y <= r[3]);
}

const out = {calibration: c, datasets: []};
for (const ds of cfg.datasets) {
    const series = new wpd.Dataset(2);
    if (ds.manual) {
        for (const p of ds.manual) series.addPixel(p[0], p[1]);
    } else {
        const det = new wpd.AutoDetectionData();
        det.imageWidth = W;
        det.imageHeight = H;
        det.fgColor = ds.fgColor || [0, 0, 0];
        det.colorDistance = ds.colorDistance == null ? 120 : ds.colorDistance;
        const mask = new Set();
        for (const r of ds.mask) {
            for (let y = Math.max(0, r[1]); y <= Math.min(H - 1, r[3]); y++) {
                for (let x = Math.max(0, r[0]); x <= Math.min(W - 1, r[2]); x++) {
                    if (!inRects(x, y, ds.exclude)) mask.add(y * W + x);
                }
            }
        }
        det.setMask(mask);
        det.generateBinaryData(imageData);
        const algo = new wpd.BlobDetectorAlgo();
        algo.setParams({minDia: ds.minDia == null ? 0 : ds.minDia,
                        maxDia: ds.maxDia == null ? 5000 : ds.maxDia});
        algo.run(det, series, axes, imageData);
    }
    const pts = [];
    for (let i = 0; i < series.getCount(); i++) {
        const p = series.getPixel(i);
        const d = axes.pixelToData(p.x, p.y);
        pts.push({px: p.x, py: p.y, x: d[0], y: d[1],
                  area: p.metadata ? p.metadata.area : null});
    }
    pts.sort((a, b) => a.x - b.x);
    out.datasets.push({name: ds.name, points: pts});
}
fs.writeFileSync(path.resolve(base, cfg.out || "result.json"), JSON.stringify(out, null, 1));
console.log(out.datasets.map(d => `${d.name}: ${d.points.length} points`).join("\n"));
