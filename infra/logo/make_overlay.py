"""Video için: eski rakamları kapatan maske + yeni rakam katmanı (3840x2160 PNG)."""
import sys, numpy as np, cairosvg, io
from PIL import Image, ImageFilter
from digits import digit_paths
end = Image.open(sys.argv[1]).convert('RGB')
a = np.array(end.convert('L'))
old = np.zeros_like(a, bool); old[650:1510, 3140:3730] = a[650:1510, 3140:3730] > 60
m = Image.fromarray((old * 255).astype('uint8')).filter(ImageFilter.MaxFilter(9))
bg = Image.new('RGBA', end.size, (26, 40, 52, 255)); bg.putalpha(m); bg.save('cover.png')
paths, _ = digit_paths()
svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160"><g fill="#FFFFFF">' + ''.join(f'<path d="{p}"/>' for p in paths) + '</g></svg>'
cairosvg.svg2png(bytestring=svg.encode(), write_to='digits.png')
prev = end.copy(); prev.paste(bg, (0, 0), bg); d = Image.open('digits.png'); prev.paste(d, (0, 0), d)
prev.resize((1920, 1080)).save(sys.argv[2])
