"""Decode native Krita VERSION 2 BGRA/LZF tiles into lossless RGBA PNGs.

Reads only the source .kra. No drawing, retouching, resampling or generation.
Native tile specification: KDE/krita libs/image/tiles3/swap/kis_tile_compressor_2.cpp.
"""
from __future__ import annotations
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image
import numpy as np


def lzf(data: bytes, size: int) -> bytes:
    out = bytearray()
    pos = 0
    while pos < len(data):
        ctrl = data[pos]
        pos += 1
        if ctrl < 32:
            count = ctrl + 1
            out.extend(data[pos:pos + count])
            pos += count
        else:
            count = ctrl >> 5
            offset = (ctrl & 31) << 8
            if count == 7:
                count += data[pos]
                pos += 1
            offset += data[pos]
            pos += 1
            ref = len(out) - offset - 1
            count += 2
            for i in range(count):
                out.append(out[ref + i])
    if len(out) != size:
        raise ValueError(f'LZF size mismatch: {len(out)} != {size}')
    return bytes(out)


def decode(data: bytes, defaultpixel: bytes, canvas: tuple[int, int]):
    stream = io.BytesIO(data)
    head = [stream.readline().decode('ascii').strip() for _ in range(5)]
    assert head[:4] == ['VERSION 2', 'TILEWIDTH 64', 'TILEHEIGHT 64', 'PIXELSIZE 4'], head
    count = int(head[4].split()[1])
    tiles = []
    for _ in range(count):
        x, y, compression, length = stream.readline().decode('ascii').strip().split(',')
        assert compression == 'LZF'
        payload = stream.read(int(length))
        if payload[0] == 1:
            planar = lzf(payload[1:], 64 * 64 * 4)
            raw = np.frombuffer(planar, dtype=np.uint8).reshape(4, 4096).T.tobytes()
        else:
            assert payload[0] == 0
            raw = payload[1:]
        tile = Image.frombytes('RGBA', (64, 64), raw, 'raw', 'BGRA')
        tiles.append((int(x), int(y), tile))
    assert stream.read() == b'', 'Unexpected trailing layer data'
    if not tiles:
        return Image.new('RGBA', canvas, (defaultpixel[2],defaultpixel[1],defaultpixel[0],defaultpixel[3])), (0,0)
    x0, y0 = min(t[0] for t in tiles), min(t[1] for t in tiles)
    x1, y1 = max(t[0] for t in tiles) + 64, max(t[1] for t in tiles) + 64
    if defaultpixel[3]:
        x0,y0=min(0,x0),min(0,y0)
        x1,y1=max(canvas[0],x1),max(canvas[1],y1)
    image = Image.new('RGBA', (x1-x0, y1-y0), (defaultpixel[2],defaultpixel[1],defaultpixel[0],defaultpixel[3]))
    for x,y,tile in tiles:
        image.paste(tile, (x-x0,y-y0))
    bbox = image.getbbox()
    if bbox:
        return image.crop(bbox), (x0+bbox[0],y0+bbox[1])
    return Image.new('RGBA',(1,1)), (x0,y0)


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)
    ns = {'k':'http://www.calligra.org/DTD/krita'}
    manifest = {'source':str(src.as_posix()),'format':'Krita native RGBA8 tiles converted losslessly to PNG', 'positionConvention':'x,y locate cropped PNG top-left on original canvas; layers ordered front to back', 'groups':[]}
    with zipfile.ZipFile(src) as z:
        root=ET.fromstring(z.read('maindoc.xml'))
        doc=root.find('k:IMAGE',ns)
        canvas=(int(doc.get('width')),int(doc.get('height')))
        manifest['width'],manifest['height']=canvas
        manifest['fps']=int(doc.find('k:animation/k:framerate',ns).get('value'))
        manifest['nativeAnimationKeyframes']=False
        manifest['nativeTimeline']={'from':0,'to':100}
        for group in doc.find('k:layers',ns):
            if not group.get('name','').startswith('Escena '):
                continue
            scene=int(group.get('name').split()[-1])
            groupdata={'name':group.get('name'),'scene':scene,'layers':[]}
            groupdir=dst/f'scene-{scene}'
            groupdir.mkdir(exist_ok=True)
            for order, node in enumerate(group.find('k:layers',ns)):
                name=node.get('name')
                filename=node.get('filename')
                slug=re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')
                output=groupdir/f'{slug}.png'
                nativepath=f'intro/layers/{filename}'
                im,origin=decode(z.read(nativepath),z.read(nativepath+'.defaultpixel'),canvas)
                x,y=origin[0]+int(node.get('x',0)),origin[1]+int(node.get('y',0))
                im.save(output)
                groupdata['layers'].append({'name':name,'sourceLayer':filename,'file':output.relative_to(dst).as_posix(),'x':x,'y':y,'width':im.width,'height':im.height,'opacity':int(node.get('opacity',255))/255,'visible':node.get('visible')=='1','reference':name.isdigit(),'order':order})
                print(f'{scene}/{name}: ({x},{y}) {im.size}',flush=True)
            manifest['groups'].append(groupdata)
        manifest['groups'].sort(key=lambda g:g['scene'])
    (dst/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')


if __name__=='__main__':
    main()
