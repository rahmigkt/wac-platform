"""'20/27' bloğu: Montserrat (ağırlık W) rakamları, video ve SVG için ortak geometri.
Koordinatlar video pikseli (3840x2160 son kare): blok x 3166-3700, y 677-1482."""
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from pathlib import Path
FONT = Path(__file__).resolve().parents[2] / 'site/assets/fonts/Montserrat.ttf'
W = 600
BX0, BX1, BY0, BY1, GAP = 3166, 3700, 677, 1482, 65

def digit_paths(weight=W):
    f = instantiateVariableFont(TTFont(FONT), {'wght': weight})
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    names = {c: cmap[ord(c)] for c in '207'}
    def bounds(c):
        bp = BoundsPen(gs); gs[names[c]].draw(bp); return bp.bounds
    b0 = bounds('0'); capH = b0[3] - b0[1]
    rows = [('2', '0'), ('2', '7')]
    gw = max(bounds(c)[2] - bounds(c)[0] for c in '207')
    GX = 56
    s = min((BY1 - BY0 - GAP) / 2 / capH, ((BX1 - BX0) - GX) / 2 / gw)
    rowH = capH * s
    colw = gw * s
    gapx = GX
    y0 = BY0 + ((BY1 - BY0) - (2 * rowH + GAP)) / 2
    out = []
    for ri, r in enumerate(rows):
        ytop = y0 + ri * (rowH + GAP)
        for ci, c in enumerate(r):
            bx = bounds(c)
            w = (bx[2] - bx[0]) * s
            x = BX0 + ci * (colw + gapx) + (colw - w) / 2  # hücrede ortala
            if ci == 1: x = BX0 + colw + gapx + (colw - w)  # sağ sütun sağa yaslı
            pen = SVGPathPen(None)
            tp = TransformPen(pen, (s, 0, 0, -s, x - bx[0] * s, ytop + b0[3] * s))
            gs[names[c]].draw(tp)
            out.append(pen.getCommands())
    return out, gapx
if __name__ == '__main__':
    p, g = digit_paths(); print(len(p), round(g, 1))
