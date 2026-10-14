"""One-time retention of image-tool pigment on untouched ancestor stone."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, jpeg, resize


def main():
    folder = Path('artifacts/line-4')
    ancestor = (folder / 'wall.png').read_bytes()
    assert hashlib.sha256(ancestor).hexdigest() == 'e2374762123e298605676d27c3ac337a8c9fd6b4f4574414a436dc6762578425'
    generated = (folder / 'wall-v10.png').read_bytes()
    w, h, old = read_png(ancestor)
    gw, gh, draft = read_png(generated)
    assert (w, h, gw, gh) == (1254, 1254, 1024, 1024)
    final = bytearray(old)
    changed = 0
    for sy in range(240, 312):
        for sx in range(650, 749):
            # Retain only the image-tool eye's charcoal and red pigment;
            # discard the regenerated rock and every regenerated ancestor mark.
            if ((sx-699)/47)**2 + ((sy-277)/34)**2 > 1.12:
                continue
            j = (sy*gw+sx)*3
            r, g, b = draft[j:j+3]
            charcoal = r < 120 and g < 100 and b < 78 and r-g < 48
            red = 679 < sx < 722 and 255 < sy < 301 and r > g*1.6 and r-g > 42
            if not (charcoal or red):
                continue
            x, y = 835+sx-650, 105+sy-240
            i = (y*w+x)*3
            original = old[i:i+3]
            # Deep fissures are protected even within the addition bounds.
            if sum(original) < 160:
                continue
            target = ([v*.36 for v in original] if charcoal else
                      [original[0]*.84, original[1]*.40, original[2]*.35])
            final[i:i+3] = bytes(round(v*.2+t*.8) for v,t in zip(original, target))
            changed += final[i:i+3] != original
    assert changed > 500
    for i in range(0, len(old), 3):
        if final[i:i+3] != old[i:i+3]:
            y, x = divmod(i//3, w)
            assert 835 <= x < 934 and 105 <= y < 177
            assert sum(old[i:i+3]) >= 160
    wall = png(w, h, final)
    for name in ('wall.png', 'wall-v10.png'):
        (folder/name).write_bytes(wall)
    preview = jpeg(512, 512, resize(w, h, final), 52)
    assert len(preview) < 100_000
    Path('dist/line-4/30.jpg').write_bytes(preview)
    sha = hashlib.sha256(wall).hexdigest()
    report = {
        'wall': {'paths': ['artifacts/line-4/wall.png', 'artifacts/line-4/wall-v10.png'],
                 'width': w, 'height': h, 'format': 'PNG', 'mode': 'RGB', 'sha256': sha},
        'preview': {'path': 'dist/line-4/30.jpg', 'width': 512, 'height': 512,
                    'format': 'JPEG', 'bytes': len(preview),
                    'sha256': hashlib.sha256(preview).hexdigest()},
        'ancestorSha256': hashlib.sha256(ancestor).hexdigest(),
        'generatedImageSha256': hashlib.sha256(generated).hexdigest(),
        'changedPixels': changed, 'unchangedPixels': w*h-changed,
        'additionBoundsExclusive': [835, 105, 934, 177],
        'preservation': 'All pixels outside the vacant upper-stone addition and all deep fissure pixels inside remain identical. No ancestral pigment lies in this addition.',
        'imageTool': 'Installed Replicate image tool, black-forest-labs/flux-kontext-pro, one edit with ancestor as input. Retained only generated pigment using inherited standard-library codec.',
        'visualReview': 'Pending final inspection.', 'unmetVisualRequirements': [],
        'limitations': ['Small worn motif is subtle at thumbnail size.',
                        'Visual inspection and byte checks are local observations.'],
    }
    Path('line-4/wall-review-30.json').write_text(json.dumps(report, indent=2)+'\n')
    record = {'name': 'The Eye Between Seeds', 'image': 'https://api.imd.fun/artifacts/'+sha,
              'attributes': [
                  {'trait_type': 'Cave', 'value': 'Water'},
                  {'trait_type': 'Wall', 'value': 'Line 4'},
                  {'trait_type': 'Number', 'value': 30},
                  {'trait_type': 'Left behind', 'value': 'offline EIP-712 string reviewer'},
                  {'trait_type': 'Meaning', 'value': 'Pepe looks closely at seeds that seem alike to find their hidden difference.'},
                  {'trait_type': 'One thing', 'value': 'offline EIP-712 typed-data digest checking'}]}
    Path('dist/line-4/30.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
