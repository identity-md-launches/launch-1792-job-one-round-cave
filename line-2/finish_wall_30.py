"""Keep exact ancestor outside the new generated pigment, including deep cracks."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

base = Path('artifacts/line-2/wall.png')
target = Path('artifacts/line-2/wall-v10.png')
ancestor = base.read_bytes()
assert hashlib.sha256(ancestor).hexdigest() == 'eb73ac72acdcb9d58e134520f36433b5f28670f0148bba8c37ac0cde295b4086'
w, h, old = read_png(ancestor)
draft = target.read_bytes()
dw, dh, generated = read_png(draft)
assert w == h == 1254 and dw == dh
scaled = resize(dw, dh, generated, w)
final = bytearray(old)
x0, y0, width, height = 220, 670, 190, 145
changed = 0
for y in range(y0, y0+height):
    for x in range(x0, x0+width):
        i = (y*w+x)*3
        rock = old[i:i+3]
        r, g, b = scaled[i:i+3]
        if max(rock) < 85 or (x*19+y*31) % 17 == 0:
            continue
        # Isolate dark charcoal and red-ochre stroke from generated bare stone.
        charcoal = max(r,g,b) < 125 and sum(rock)-r-g-b > 80
        ochre = r > 80 and g < r*.52 and b < r*.38 and rock[1]-g > 25
        if charcoal or ochre:
            pigment = (48, 33, 21) if charcoal else (139, 54, 24)
            alpha = .73 if charcoal else .65
            for c in range(3):
                final[i+c] = round(rock[c]*(1-alpha)+pigment[c]*alpha)
            changed += 1
assert changed > 1000
for y in range(h):
    for x in range(w):
        i=(y*w+x)*3
        if final[i:i+3] != old[i:i+3]:
            assert x0 <= x < x0+width and y0 <= y < y0+height
encoded = png(w,h,final)
base.write_bytes(encoded)
target.write_bytes(encoded)
preview = jpeg(512,512,resize(w,h,final),52)
assert len(preview) <= 100000
Path('dist/line-2/30.jpg').write_bytes(preview)
review = {'number':30,'ancestor_sha256':hashlib.sha256(ancestor).hexdigest(),
          'sha256':hashlib.sha256(encoded).hexdigest(),
          'wall':{'paths':[str(base),str(target)],'width':w,'height':h,'format':'PNG','mode':'RGB'},
          'preview':{'path':'dist/line-2/30.jpg','width':512,'height':512,'format':'JPEG','bytes':len(preview)},
          'addition_region':{'x':x0,'y':y0,'width':width,'height':height},
          'changed_pixels':changed,'unchanged_pixels':w*h-changed,
          'outside_region_pixel_identical':True,'dark_cracks_preserved':True,
          'generation_tool':'mcp__image__edit_image','draft_sha256':hashlib.sha256(draft).hexdigest(),
          'draft_retained':False,'visual_review':'pending inspection','unmet_visual_requirements':[]}
Path('line-2/wall-review-30.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps(review,indent=2))
