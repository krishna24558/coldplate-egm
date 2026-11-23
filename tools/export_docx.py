"""Export docs/final_report.md to docs/final_report.docx (pandoc, then python-docx clean-up).

Command (from the repository folder):

    python tools/export_docx.py                 # writes docs/final_report.docx
    python tools/export_docx.py --word-pdf      # also: page count and a PDF from Microsoft Word
    python tools/export_docx.py --workdir DIR   # keep the intermediate files in DIR

Required packages (not in requirements.txt; only this script needs them):

    pip install pypandoc_binary python-docx

``pypandoc_binary`` ships its own pandoc executable. The export of 2026-11-22 used
pypandoc_binary 1.17 (pandoc 3.9), python-docx 1.2.0 and lxml 6.1.3 on Python 3.12.
A pandoc already on PATH, or one named by the ``PANDOC`` environment variable, also works.
``--word-pdf`` is Windows only and needs Microsoft Word (driven through PowerShell COM);
Word's page count is the one quoted in docs/project_status.md.

What the script does. The Markdown file itself is never changed; a preprocessed copy is
converted:

1. The title block (first heading and the lines under it) becomes pandoc YAML metadata
   (title, subtitle, authors). HTML comments are removed.
2. Pipe-table separator rows are rewritten with dash counts in proportion to the cell
   text, so pandoc gives the text-heavy columns more width.
3. Every display equation must carry ``\\tag{k}`` with k = 1..n in order. pandoc drops
   ``\\tag``, so the tags are removed here and the numbers added back in step 5.
4. Images are set to the full text width (6.5 in on Letter with 1 in margins).
5. After pandoc: Letter paper, 1 in margins, Calibri 10.5 pt body (tables 8.5 pt,
   captions 9.5 pt); tables get grey borders, a shaded bold header row that repeats on
   every page, and are centred; table captions keep with the table and image paragraphs
   keep with their caption; each numbered equation is put in a borderless two-cell table,
   equation centred and "(k)" in the right-hand cell; page numbers in the footer.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "docs" / "final_report.md"
OUT = REPO / "docs" / "final_report.docx"

BODY_FONT, BODY_PT, TABLE_PT, CAPTION_PT = "Calibri", 10.5, 8.5, 9.5


def find_pandoc():
    """pandoc from $PANDOC, then from pypandoc(_binary), then from PATH."""
    if os.environ.get("PANDOC"):
        return os.environ["PANDOC"]
    try:
        import pypandoc
        return pypandoc.get_pandoc_path()
    except (ImportError, OSError):
        pass
    exe = shutil.which("pandoc")
    if exe:
        return exe
    sys.exit("pandoc not found: pip install pypandoc_binary, or set PANDOC")


# ---------------------------------------------------------------- preprocessing

def split_cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


SEP = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")


def widen_tables(lines):
    """Set the dash counts of each pipe-table separator in proportion to the content,
    so pandoc gives wide columns to the text-heavy ones."""
    out, i = [], 0
    while i < len(lines):
        if i + 1 < len(lines) and lines[i].lstrip().startswith("|") and SEP.match(lines[i + 1].strip()):
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            rows = [split_cells(lines[i])] + [split_cells(l) for l in lines[i + 2:j]]
            n = len(rows[0])
            w = []
            for c in range(n):
                lens = [len(r[c]) if c < len(r) else 0 for r in rows]
                mean = sum(lens) / len(lens)
                w.append(max(4, min(80, int(round(0.5 * mean + 0.5 * max(lens))))))
            out.append(lines[i])
            out.append("|" + "|".join("-" * k for k in w) + "|")
            out.extend(lines[i + 2:j])
            i = j
        else:
            out.append(lines[i])
            i += 1
    return out


def preprocess(src, tmp):
    """Write the pandoc input to tmp; return (number of equation tags, number of images)."""
    lines = src.read_text(encoding="utf-8").split("\n")
    assert lines[0].startswith("# "), "first line must be the title"
    title = lines[0][2:].strip()
    i = 1
    while not lines[i].strip():
        i += 1
    block = []
    while lines[i].strip():
        block.append(lines[i].rstrip().rstrip("\\").strip())
        i += 1
    yaml = ["---", f'title: "{title}"', f'subtitle: "{block[0]}"', "author:"]
    yaml += [f'  - "{b}"' for b in block[1:]]
    yaml += ["---", ""]
    body = "\n".join(widen_tables(lines[i:]))
    body = re.sub(r"<!--.*?-->\n?", "", body, flags=re.S)
    tags = [int(t) for t in re.findall(r"\\tag\{(\d+)\}", body)]
    n_tags = len(tags)
    displays = re.findall(r"\$\$(.+?)\$\$", body, flags=re.S)
    assert tags == list(range(1, n_tags + 1)), "equation tags must run 1..n in order"
    assert len(displays) == n_tags and all("\\tag{" in m for m in displays), "one tag per display equation"
    body = re.sub(r"\s*\\tag\{\d+\}", "", body)  # numbers are added back as a right-hand table cell
    n_img = len(re.findall(r"^!\[[^\]]*\]\([^)]+\)[ \t]*$", body, flags=re.M))
    body = re.sub(r"^(!\[[^\]]*\]\([^)]+\))[ \t]*$", r"\1{width=100%}", body, flags=re.M)
    tmp.write_text("\n".join(yaml) + body, encoding="utf-8")
    return n_tags, n_img


# ---------------------------------------------------------------- reference doc

def make_reference_doc(pandoc, ref):
    subprocess.run([pandoc, "-o", str(ref), "--print-default-data-file", "reference.docx"], check=True)
    rd = Document(str(ref))
    for name in ("Normal", "Body Text", "First Paragraph", "Compact", "Author", "Subtitle", "Date"):
        try:
            st = rd.styles[name]
        except KeyError:
            continue
        st.font.name = BODY_FONT
        st.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
        if name in ("Normal", "Body Text", "First Paragraph", "Compact"):
            st.font.size = Pt(BODY_PT)
    for name in ("Title", "Heading 1", "Heading 2", "Heading 3", "Heading 4"):
        st = rd.styles[name]
        st.font.name = BODY_FONT
        st.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    rd.styles["Title"].font.size = Pt(18)
    rd.styles["Heading 1"].font.size = Pt(15)
    rd.styles["Heading 2"].font.size = Pt(12.5)
    rd.styles["Heading 3"].font.size = Pt(11)
    for name, size in (("Verbatim Char", 9.5), ("Source Code", 9.0)):
        try:
            rd.styles[name].font.size = Pt(size)
        except KeyError:
            print("style not in reference doc:", name)
    for s in rd.sections:
        s.page_width, s.page_height = Inches(8.5), Inches(11)
        s.left_margin = s.right_margin = Inches(1)
        s.top_margin = s.bottom_margin = Inches(1)
    rd.save(str(ref))


# ---------------------------------------------------------------- post-processing helpers

TBLPR = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
         "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd",
         "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription"]
TCPR = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar",
        "textDirection", "tcFitText", "vAlign", "hideMark"]
TRPR = ["cnfStyle", "divId", "gridBefore", "gridAfter", "wBefore", "wAfter", "cantSplit",
        "trHeight", "tblHeader", "tblCellSpacing", "jc", "hidden"]
MATH = "http://schemas.openxmlformats.org/officeDocument/2006/math"
CAP = re.compile(r"^(Figure \d+|Table [A-C]?\d+)\.")


def put(parent, el, order):
    """Insert el into parent in schema order, replacing an element with the same tag."""
    tag = el.tag
    for old in parent.findall(tag):
        parent.remove(old)
    name = tag.split("}")[1]
    rank = order.index(name)
    for child in parent:
        cname = child.tag.split("}")[1]
        if cname in order and order.index(cname) > rank:
            child.addprevious(el)
            return
    parent.append(el)


def mk(tag, **attrs):
    el = OxmlElement(tag)
    for k, v in attrs.items():
        el.set(qn("w:" + k), v)
    return el


def set_cell_shading(cell, hex_fill):
    put(cell._tc.get_or_add_tcPr(), mk("w:shd", val="clear", color="auto", fill=hex_fill), TCPR)


def set_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        borders.append(mk(f"w:{edge}", val="single", sz="4", space="0", color="8C8C8C"))
    put(tblPr, borders, TBLPR)
    mar = OxmlElement("w:tblCellMar")
    for edge, v in (("top", 15), ("left", 70), ("bottom", 15), ("right", 70)):
        mar.append(mk(f"w:{edge}", w=str(v), type="dxa"))
    put(tblPr, mar, TBLPR)


def repeat_header(row):
    put(row._tr.get_or_add_trPr(), mk("w:tblHeader", val="true"), TRPR)


def no_borders(tbl):
    tblPr = tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b.append(mk(f"w:{edge}", val="nil"))
    put(tblPr, b, TBLPR)
    put(tblPr, mk("w:tblLayout", type="fixed"), TBLPR)
    put(tblPr, mk("w:tblLook", val="0000", firstRow="0", lastRow="0", firstColumn="0",
                  lastColumn="0", noHBand="1", noVBand="1"), TBLPR)


def postprocess(out, n_tags):
    doc = Document(str(out))
    for name, size in (("Source Code", 9.0), ("Verbatim Char", 9.5)):
        if name in [st.name for st in doc.styles]:
            doc.styles[name].font.size = Pt(size)

    # report tables: borders, shaded bold header row repeated on each page, small font
    for t in doc.tables:
        set_table_borders(t)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for ri, row in enumerate(t.rows):
            for cell in row.cells:
                for p in cell.paragraphs:
                    pf = p.paragraph_format
                    pf.space_before = Pt(1)
                    pf.space_after = Pt(1)
                    pf.line_spacing = 1.0
                    for run in p.runs:
                        run.font.size = Pt(TABLE_PT)
                        if ri == 0:
                            run.font.bold = True
                if ri == 0:
                    set_cell_shading(cell, "E3E8EF")
        repeat_header(t.rows[0])

    # figures centred and kept with their caption; table captions kept with the table
    n_fig_cap = n_tab_cap = 0
    for p in doc.paragraphs:
        if p._p.findall(".//" + qn("w:drawing")):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.space_after = Pt(2)
            continue
        m = CAP.match(p.text)
        if m and p.runs and p.runs[0].bold:
            for run in p.runs:
                run.font.size = Pt(CAPTION_PT)
            if m.group(1).startswith("Table"):
                p.paragraph_format.keep_with_next = True
                n_tab_cap += 1
            else:
                p.paragraph_format.space_after = Pt(10)
                n_fig_cap += 1

    # numbered display equations: borderless 1 x 2 table, equation centred, "(k)" on the right
    eq_paras = [p for p in doc.element.body.iterchildren(qn("w:p"))
                if p.find(f".//{{{MATH}}}oMathPara") is not None]
    assert len(eq_paras) == n_tags, (len(eq_paras), n_tags)
    for k, p in enumerate(eq_paras, 1):
        t = doc.add_table(rows=1, cols=2)
        no_borders(t._tbl)
        p.addprevious(t._tbl)
        c0, c1 = t.rows[0].cells
        for c, w in ((c0, Inches(5.85)), (c1, Inches(0.65))):
            c.width = w
            tcPr = c._tc.get_or_add_tcPr()
            tcb = OxmlElement("w:tcBorders")
            for edge in ("top", "left", "bottom", "right"):
                tcb.append(mk(f"w:{edge}", val="nil"))
            put(tcPr, tcb, TCPR)
            put(tcPr, mk("w:vAlign", val="center"), TCPR)
        c0._tc.remove(c0.paragraphs[0]._p)
        c0._tc.append(p)
        np_ = c1.paragraphs[0]
        np_.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        np_.add_run(f"({k})").font.size = Pt(BODY_PT)

    # page numbers in the footer
    for s in doc.sections:
        fp = s.footer.paragraphs[0] if s.footer.paragraphs else s.footer.add_paragraph()
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = fp.add_run()
        for tag, attr in (("w:fldChar", {"w:fldCharType": "begin"}),
                          ("w:instrText", None),
                          ("w:fldChar", {"w:fldCharType": "end"})):
            el = OxmlElement(tag)
            if attr:
                for a, v in attr.items():
                    el.set(qn(a), v)
            else:
                el.set(qn("xml:space"), "preserve")
                el.text = "PAGE"
            run._r.append(el)
        run.font.size = Pt(9)

    doc.save(str(out))
    return n_fig_cap, n_tab_cap


def word_pdf(docx_path, pdf_path):
    """Open the .docx in Microsoft Word (PowerShell COM), return Word's page count and save a PDF."""
    q = lambda p: str(p).replace("'", "''")  # noqa: E731  (PowerShell single-quote escape)
    ps = (
        "$ErrorActionPreference = 'Stop'; $w = New-Object -ComObject Word.Application; "
        "$w.Visible = $false; try { "
        f"$d = $w.Documents.Open('{q(docx_path)}', $false, $true); $d.Repaginate(); "
        "$n = $d.ComputeStatistics(2); "  # 2 = wdStatisticPages
        f"$d.ExportAsFixedFormat('{q(pdf_path)}', 17); "  # 17 = wdExportFormatPDF
        "$d.Close($false); Write-Output $n } finally { $w.Quit() }"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Word export failed: {r.stderr.strip()[:1000]}")
    return int(r.stdout.strip().splitlines()[-1])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workdir", type=Path, help="folder for the intermediate files (default: a new temp folder)")
    ap.add_argument("--word-pdf", action="store_true",
                    help="Windows + Microsoft Word: print Word's page count and save final_report_word.pdf in the work folder")
    args = ap.parse_args()

    work = args.workdir or Path(tempfile.mkdtemp(prefix="export_docx_"))
    work.mkdir(parents=True, exist_ok=True)
    pandoc = find_pandoc()

    tmp = work / "final_report_export.md"
    n_tags, n_img = preprocess(SRC, tmp)
    print(f"preprocessed: {n_tags} equation tags, {n_img} images")

    ref = work / "reference.docx"
    make_reference_doc(pandoc, ref)

    cmd = [pandoc, str(tmp),
           "-f", "commonmark_x-implicit_figures-superscript-subscript",
           "-t", "docx", "--reference-doc", str(ref), "--shift-heading-level-by=-1",
           "--resource-path", str(REPO / "docs"), "-o", str(OUT)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print("pandoc exit", r.returncode, r.stderr.strip()[:2000])
    r.check_returncode()

    n_fig_cap, n_tab_cap = postprocess(OUT, n_tags)

    doc = Document(str(OUT))
    widths = [s.width.inches for s in doc.inline_shapes]
    print(f"tables {len(doc.tables)} (incl. {n_tags} equation-number tables), figure captions {n_fig_cap}, "
          f"table captions {n_tab_cap}, images {len(widths)} (max width {max(widths):.2f} in), "
          f"display equations {doc.element.xml.count('<m:oMathPara>')}")
    print("written", OUT, OUT.stat().st_size // 1024, "kB; intermediate files in", work)

    if args.word_pdf:
        pdf = work / "final_report_word.pdf"
        print("Word page count:", word_pdf(OUT, pdf), "; PDF:", pdf)


if __name__ == "__main__":
    main()
