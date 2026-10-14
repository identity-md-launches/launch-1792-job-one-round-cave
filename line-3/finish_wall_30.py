"""Place generated earth pigment on vacant stone, preserving ancestor pixels."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

ROOT = Path(__file__).resolve().parent.parent
ANCESTOR = 'f5a6dde219059ae9e85c6cd63624dc315410bffa752f97a7bf0b351ad6f31af5'
PROMPT = 'A short chain of irregular joined pebbles in worn charcoal, red and yellow ochre, and chalk white; isolated cave pigment on white. No text, numbers, arrows, hands, figures, logos or frames.'


def main():
    wall = ROOT/'artifacts/line-3/wall.png'
    target = ROOT/'artifacts/line-3/wall-v10.png'
    ancestor = wall.read_bytes()
    assert hashlib.sha256(ancestor).hexdigest() == ANCESTOR
    w, h, old = read_png(ancestor)
    draft = target.read_bytes()
    gw, gh, generated = read_png(draft)
    assert (w,h) == (1254,1254)
    def pigment(x,y):
        red,green,blue = generated[(y*gw+x)*3:(y*gw+x)*3+3]
        charcoal = max(red,green,blue) < 130
        ochre = red > 85 and green < red*.87 and blue < red*.65
        return charcoal or ochre
    points = [(x,y) for y in range(gh) for x in range(gw) if pigment(x,y)]
    sx0,sy0 = min(x for x,y in points),min(y for x,y in points)
    sx1,sy1 = max(x for x,y in points)+1,max(y for x,y in points)+1
    # Vacant narrow stone below the bowl, above the ancestor pebbles.
    x0,y0,width,height = 625,592,235,33
    final = bytearray(old)
    changed = 0
    for dy in range(height):
        for dx in range(width):
            x,y = x0+dx,y0+dy
            i = (y*w+x)*3
            rock = old[i:i+3]
            if max(rock) < 80: continue
            xa,xb = sx0+dx*(sx1-sx0)//width,sx0+(dx+1)*(sx1-sx0)//width
            ya,yb = sy0+dy*(sy1-sy0)//height,sy0+(dy+1)*(sy1-sy0)//height
            color,coverage = [0,0,0],0
            for gy in range(ya,yb):
                for gx in range(xa,xb):
                    if not pigment(gx,gy): continue
                    red,green,blue = generated[(gy*gw+gx)*3:(gy*gw+gx)*3+3]
                    selected = ((49,37,24) if max(red,green,blue) < 130 else
                                (157,69,30) if green < red*.64 else (165,116,47))
                    coverage += 1
                    for c in range(3): color[c] += selected[c]
            if not coverage: continue
            alpha = .82*coverage/((xb-xa)*(yb-ya))
            light = min(1.1,max(.55,sum(rock)/(3*135)))
            for c in range(3):
                final[i+c] = round(rock[c]*(1-alpha)+color[c]/coverage*light*alpha)
            changed += final[i:i+3] != rock
    assert changed > 300
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            if not (x0<=x<x0+width and y0<=y<y0+height) or max(old[i:i+3])<80:
                assert final[i:i+3] == old[i:i+3]
    encoded = png(w,h,final)
    target.write_bytes(encoded);wall.write_bytes(encoded)
    thumbnail = resize(w,h,final)
    quality = 52
    preview = jpeg(512,512,thumbnail,quality)
    while len(preview)>100000 and quality>10:
        quality -= 5;preview = jpeg(512,512,thumbnail,quality)
    assert len(preview)<=100000
    (ROOT/'dist/line-3/30.jpg').write_bytes(preview)
    review = {'ancestorSha256':ANCESTOR,'ancestorDimensions':[w,h],
              'wallDimensions':[w,h],'wallFormat':'PNG','wallMode':'RGB',
              'wallSha256':hashlib.sha256(encoded).hexdigest(),
              'draftSha256':hashlib.sha256(draft).hexdigest(),'draftRetained':False,
              'additionRectangle':[x0,y0,width,height],'changedPixels':changed,
              'unchangedPixels':w*h-changed,'allPixelsOutsideAdditionUnchanged':True,
              'deepCracksProtected':True,'previewDimensions':[512,512],
              'previewFormat':'JPEG','previewBytes':len(preview),'previewQuality':quality,
              'imageTool':'mcp__image__generate','promptSummary':PROMPT,
              'reviewStatus':'requires visual inspection','unmetVisualRequirements':[]}
    (ROOT/'line-3/wall-review-30.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__ == '__main__': main()
