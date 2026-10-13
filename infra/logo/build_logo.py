"""WAC katlanmış kâğıt logosunun geometrik yeniden çizimi.

Tek ızgara: yükseklik 100, bütün eğik kenarlar 60° (yatay kayma k = tan 30°),
bant genişliği W, boşluk G. Çıktı: SVG (açık/koyu, logo ve lockup) ve PNG.
"""
import math
from pathlib import Path

import cairosvg
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

K = math.tan(math.radians(30))
H = 100.0
W = 28.0          # bant yatay genişliği
G = 8.0           # bantlar arası boşluk
BAR = 22.0        # C kollarının kalınlığı
CV = 38.0         # C kırılma noktasının yüksekliği
CW = 118.0        # C genişliği


def V(cx):
    i = H - W / K
    return Polygon([(cx - K * H, 0), (cx - K * H + W, 0), (cx, i), (cx + K * H - W, 0), (cx + K * H, 0), (cx, H)])


def LAMBDA(ax):
    i = W / K
    return Polygon([(ax, 0), (ax + K * H, H), (ax + K * H - W, H), (ax, i), (ax - K * H + W, H), (ax - K * H, H)])


cx1 = K * H
cx2 = cx1 + 55.0
ax = cx2 + K * H + G
vx = ax + G + K * CV
xe = vx + CW

v1, v2 = V(cx1), V(cx2)
rest = v1.difference(v2)
parts = [p for p in getattr(rest, 'geoms', [rest]) if p.bounds[3] >= H - 0.01]
v1_vis = unary_union(parts)
w_fold = v1.intersection(v2)
w_fold = unary_union([p for p in getattr(w_fold, 'geoms', [w_fold]) if p.area > 1])

lam = LAMBDA(ax)
counter = Polygon([(ax, W / K), (ax + K * H - W, H), (ax - K * H + W, H)])
cross = counter.intersection(box(-1e3, 74, 1e3, 96)).buffer(-G / 2, join_style=2)
cross = cross.intersection(box(-1e3, 74, 1e3, 96))
# çapraz bant yalnızca sol bacağa yaslanır
cross = Polygon([(ax - K * (H - 74) + W - G * .2, 74), (ax + K * (74 - W / K) * 1 - G, 74),
                 (ax + K * (96 - W / K) - G, 96), (ax - K * (H - 96) + W - G * .2, 96)]) if False else cross

upper = Polygon([(vx, CV), (vx + K * CV, 0), (vx + K * CV + W, 0), (vx + W, CV)])
lower = Polygon([(vx, CV), (vx + W, CV), (vx + W + K * (H - CV), H), (vx + K * (H - CV), H)])
c_arm = unary_union([upper, lower]).buffer(0)
top_bar = Polygon([(vx + K * CV, 0), (xe, 0), (xe - K * BAR, BAR), (vx + K * CV, BAR)]).difference(c_arm)
bot_bar = Polygon([(vx + K * (H - CV - BAR), H - BAR), (xe, H - BAR), (xe - K * BAR, H), (vx + K * (H - CV), H)]).difference(c_arm)

W_TOTAL = xe
PAD = 0


def path(g):
    out = []
    for p in getattr(g, 'geoms', [g]):
        c = list(p.exterior.coords)[:-1]
        out.append('M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in c) + 'Z')
    return ' '.join(out)


def mark(face, shade, uid):
    s = f'''<defs>
<linearGradient id="{uid}a" gradientUnits="userSpaceOnUse" x1="{cx1+20}" y1="40" x2="{cx1+5}" y2="90"><stop offset="0" stop-color="{shade}"/><stop offset="1" stop-color="{face}"/></linearGradient>
<linearGradient id="{uid}b" gradientUnits="userSpaceOnUse" x1="{cx2-20}" y1="40" x2="{cx2-5}" y2="60"><stop offset="0" stop-color="{shade}"/><stop offset="1" stop-color="{face}" stop-opacity="0"/></linearGradient>
<linearGradient id="{uid}c" gradientUnits="userSpaceOnUse" x1="{ax-30}" y1="85" x2="{ax+20}" y2="85"><stop offset="0" stop-color="{face}"/><stop offset="1" stop-color="{shade}"/></linearGradient>
<linearGradient id="{uid}d" gradientUnits="userSpaceOnUse" x1="{vx+40}" y1="0" x2="{xe}" y2="0"><stop offset="0" stop-color="{shade}"/><stop offset=".45" stop-color="{face}"/></linearGradient>
<linearGradient id="{uid}e" gradientUnits="userSpaceOnUse" x1="{vx+60}" y1="0" x2="{xe}" y2="0"><stop offset="0" stop-color="{shade}"/><stop offset=".5" stop-color="{face}"/></linearGradient>
<linearGradient id="{uid}f" gradientUnits="userSpaceOnUse" x1="{ax}" y1="20" x2="{ax-45}" y2="100"><stop offset="0" stop-color="{face}"/><stop offset=".75" stop-color="{face}"/><stop offset="1" stop-color="{shade}"/></linearGradient>
</defs>
<path d="{path(v1_vis)}" fill="url(#{uid}a)"/>
<path d="{path(v2)}" fill="{face}"/>
<path d="{path(w_fold)}" fill="url(#{uid}b)" opacity=".9"/>
<path d="{path(lam)}" fill="url(#{uid}f)"/>
<path d="{path(cross)}" fill="url(#{uid}c)"/>
<path d="{path(top_bar)}" fill="url(#{uid}d)"/>
<path d="{path(bot_bar)}" fill="url(#{uid}e)"/>
<path d="{path(c_arm)}" fill="{face}"/>'''
    return s


THEMES = {
    'light': dict(face='#FFFFFF', shade='#C9D1DC', text='#FFFFFF', rule='#FFFFFF'),   # koyu zemin üstü
    'dark': dict(face='#0E2A3D', shade='#4A6276', text='#0E2A3D', rule='#0E2A3D'),    # açık zemin üstü
}
OUT = Path(__file__).resolve().parents[2] / 'site' / 'assets'


def svg_mark(t):
    th = THEMES[t]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_TOTAL:.2f} {H:.0f}" '
            f'role="img" aria-label="WAC">{mark(th["face"], th["shade"], "m" + t)}</svg>')


def svg_lockup(t):
    th = THEMES[t]
    x0 = W_TOTAL + 14
    tx = x0 + 14
    lines = [('WAC', 14, 600, 0), ('2027', 14, 600, 0), ('WORLD', 9.2, 500, 0),
             ('AEROSPACE', 9.2, 500, 0), ('CONGRESS', 9.2, 500, 0)]
    ys = [18, 38, 62, 78, 94]
    txt = ''.join(f'<text x="{tx}" y="{y}" font-family="Montserrat, Arial, sans-serif" font-size="{s}" '
                  f'font-weight="{fw}" letter-spacing="{s*0.32:.2f}" fill="{th["text"]}">{l}</text>'
                  for (l, s, fw, _), y in zip(lines, ys))
    width = tx + 92
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.2f} {H:.0f}" role="img" '
            f'aria-label="WAC 2027 — World Aerospace Congress">{mark(th["face"], th["shade"], "l" + t)}'
            f'<rect x="{x0}" y="0" width="1.2" height="{H}" fill="{th["rule"]}"/>{txt}</svg>')


for t in THEMES:
    for name, fn in (('wac-logo', svg_mark), ('wac-lockup', svg_lockup)):
        svg = fn(t)
        p = OUT / f'{name}-{t}.svg'
        p.write_text(svg)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(OUT / f'{name}-{t}.png'), output_height=456)
print('ok', round(W_TOTAL, 1))
