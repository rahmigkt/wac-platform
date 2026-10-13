"""WAC logosu: PDF'teki vektör yollar birebir + videodaki '20/27' bloğu (ölçülerek)."""
import re, sys
from pathlib import Path
import cairosvg
src = Path(sys.argv[1]).read_text()
paths = re.findall(r' d="([^"]+)"', src)
X0, Y0, X1, Y1 = 444.85, 613.27, 4208.67, 1654.17
S = 1 / 0.7772                       # video px -> PDF birimi
def vx(x): return X0 + (x - 138) * S
def vy(y): return Y0 + (y - 675) * S
def two(x, y):
    r = lambda a, b, c, d: f'M{vx(x+a):.1f},{vy(y+b):.1f}H{vx(x+c):.1f}V{vy(y+d):.1f}H{vx(x+a):.1f}Z'
    return r(0,0,230,82)+r(148,82,230,145)+r(0,145,230,226)+r(0,226,82,289)+r(0,289,230,371)
def zero(x, y):
    return (f'M{vx(x):.1f},{vy(y):.1f}H{vx(x+230):.1f}V{vy(y+371):.1f}H{vx(x):.1f}Z'
            f'M{vx(x+82):.1f},{vy(y+82):.1f}V{vy(y+289):.1f}H{vx(x+149):.1f}V{vy(y+82):.1f}Z')
def seven(x, y):
    return (f'M{vx(x):.1f},{vy(y):.1f}H{vx(x+230):.1f}L{vx(x+176):.1f},{vy(y+371):.1f}'
            f'H{vx(x+69):.1f}L{vx(x+112):.1f},{vy(y+82):.1f}H{vx(x):.1f}Z')
digits = two(3166,677) + zero(3470,677) + two(3166,1112) + seven(3470,1112)
DX1 = vx(3700)
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
for theme, fill in (('light', '#FFFFFF'), ('dark', '#0E2A3D')):
    mark = ''.join(f'<path d="{d}"/>' for d in paths)
    for name, x1, extra, label in (('wac-mark', X1, '', 'WAC'),
                                   ('wac-lockup', DX1, f'<path fill-rule="evenodd" d="{digits}"/>', 'WAC 2027')):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{X0:.2f} {Y0:.2f} {x1-X0:.2f} {Y1-Y0:.2f}" '
               f'role="img" aria-label="{label}"><g fill="{fill}">{mark}{extra}</g></svg>')
        (out / f'{name}-{theme}.svg').write_text(svg)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(out / f'{name}-{theme}.png'), output_height=400)
print('ok')
