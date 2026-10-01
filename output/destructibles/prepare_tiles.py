"""Split the overhead source into editable gameplay PNGs (requires Pillow)."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
KINDS = ('crate', 'barrel', 'open_box', 'stool', 'skull', 'bones')
source = Image.open(Path(__file__).with_name('objetos-estados-cenital.png')).convert('RGBA')
source.putalpha(source.getchannel('A').point(lambda a: 255 if a >= 128 else 0))
for row, kind in enumerate(KINDS):
    dest = ROOT / 'assets/images/objects/destructibles'
    dest.mkdir(parents=True, exist_ok=True)
    frames = []
    cells = [source.crop((round(col * source.width / 3), row * 256,
                          round((col + 1) * source.width / 3), (row + 1) * 256)) for col in range(3)]
    boxes = [im.getbbox() for im in cells[:2]]
    width = max(b[2] - b[0] for b in boxes)
    height = max(b[3] - b[1] for b in boxes)
    scale = 28 / max(width, height)
    for name, im, box in zip(('intact', 'damaged'), cells, boxes):
        crop = im.crop(box)
        crop = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.Resampling.NEAREST)
        tile = Image.new('RGBA', (32, 32))
        tile.paste(crop, ((32-crop.width)//2, (32-crop.height)//2))
        frames.append(tile)
    # Connected alpha components preserve the actual illustrated broken pieces.
    im = cells[2]
    alpha = im.getchannel('A')
    remaining = {(x, y) for y in range(im.height) for x in range(im.width) if alpha.getpixel((x, y))}
    components = []
    while remaining:
        seed = min(remaining, key=lambda p: (p[1], p[0]))
        remaining.remove(seed)
        pending, component = [seed], [seed]
        while pending:
            x, y = pending.pop()
            for p in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
                if p in remaining:
                    remaining.remove(p)
                    pending.append(p)
                    component.append(p)
        if len(component) >= 80:
            components.append(component)
    for index, points in enumerate(components):
        xs, ys = zip(*points)
        crop = im.crop((min(xs), min(ys), max(xs)+1, max(ys)+1))
        crop = crop.resize((max(2, round(crop.width*scale)), max(2, round(crop.height*scale))), Image.Resampling.NEAREST)
        tile = Image.new('RGBA', (32, 32))
        tile.paste(crop, ((32-crop.width)//2, (32-crop.height)//2))
        frames.append(tile)
    sheet = Image.new('RGBA', (32*len(frames), 32))
    for index, frame in enumerate(frames):
        sheet.paste(frame, (index*32, 0))
    sheet.save(dest / (kind + '.png'))
    print(kind, len(components), 'fragments')
