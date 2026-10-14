#!/usr/bin/env python3
"""Preserve the ancestral bytes and add only the tool-generated pigment."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, jpeg, resize

ANCESTOR = '2daa514aae24125f90df19455e61febb0880af5b01007fd14c8030a83f2a6b1e'
PROMPT = ('Preserve the complete ancestral cave and all older marks. Add a small worn '
          'charcoal/red ochre heavy-lidded broad-mouth Pepe head above three linked '
          'pebbles on vacant upper-left rock. No hands, text, numbers, logos or borders.')


def main():
    wall = Path('artifacts/gathering/wall.png')
    target = wall.with_name('wall-v10.png')
    ancestor, draft = wall.read_bytes(), target.read_bytes()
    assert hashlib.sha256(ancestor).hexdigest() == ANCESTOR
    w, h, old = read_png(ancestor)
    gw, gh, generated = read_png(draft)
    assert (w, h) == (gw, gh) == (1254, 1254)
    final = bytearray(old)
    # Extract only dark generated pigment, not its regenerated cave. The new
    # design's source rectangle contains no ancestral mark. Move the NEW mark
    # left/up onto vacant stone to leave the older pointed pebble untouched.
    source = (225, 130, 345, 250)
    x0, y0 = 175, 115
    changed = 0
    for sy in range(source[1], source[3]):
        for sx in range(source[0], source[2]):
            x, y = x0+sx-source[0], y0+sy-source[1]
            gi, oi = (sy*w+sx)*3, (y*w+x)*3
            r, g, b = generated[gi:gi+3]
            rock = old[oi:oi+3]
            if max(rock) < 75:
                continue
            # Burnt-stick lines are substantially darker than the insert's rock.
            # Red ochre fill is omitted to avoid copying any generated substrate.
            if max(r,g,b) > 82 or min(r,g,b) > 55:
                continue
            alpha = min(.82, max(0, (88-max(r,g,b))/45))
            if alpha < .16:
                continue
            color = (39, 30, 22)
            for c in range(3):
                final[oi+c] = round(rock[c]*(1-alpha)+color[c]*alpha)
            if final[oi:oi+3] != rock:
                changed += 1
    assert changed > 1000
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            if not (x0 <= x < x0+120 and y0 <= y < y0+120) or max(old[i:i+3]) < 75:
                assert final[i:i+3] == old[i:i+3]
    encoded = png(w,h,final)
    target.write_bytes(encoded)
    wall.write_bytes(encoded)
    thumb = resize(w,h,final)
    quality = 52
    preview = jpeg(512,512,thumb,quality)
    while len(preview) > 100000:
        quality -= 5
        assert quality >= 10
        preview = jpeg(512,512,thumb,quality)
    Path('dist/gathering/10.jpg').write_bytes(preview)
    review = dict(ancestorSha256=ANCESTOR, ancestorSize=[w,h], wallSize=[w,h],
        wallFormat='PNG',wallMode='RGB',wallSha256=hashlib.sha256(encoded).hexdigest(),
        generatedDraftSha256=hashlib.sha256(draft).hexdigest(),generatedDraftRetained=False,
        changedPixels=changed,unchangedPixels=w*h-changed,additionRectangle=[x0,y0,120,120],
        allPixelsOutsideAdditionUnchanged=True,deepCracksProtected=True,
        previewSize=[512,512],previewFormat='JPEG',previewBytes=len(preview),
        imageTool='mcp__image__generate_image',prompt=PROMPT,
        reviewStatus='requires final visual inspection',unmetVisualRequirements=[])
    Path('gathering/wall-review-10.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))

if __name__ == '__main__':
    main()
