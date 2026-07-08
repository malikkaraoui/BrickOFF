"""Rendu des labels FINAUX avec indices L# (pour corrections post-vérification PO)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path("data/processed/realworld_piles/decision")
name = sys.argv[1]; out = sys.argv[2]
im = Image.open(root/"images"/name).convert("RGB")
scale = 1600/max(im.size)
if scale < 1: im = im.resize((int(im.width*scale), int(im.height*scale)))
d = ImageDraw.Draw(im); W,H = im.size
try: font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
except Exception: font = ImageFont.load_default()
lines = (root/"labels"/(Path(name).stem+".txt")).read_text().splitlines()
for i, line in enumerate(l for l in lines if l.strip()):
    hard = line.startswith("# hard")
    p = line.replace("# hard ","").split()
    _, cx, cy, w, h = map(float, p)
    x1,y1 = (cx-w/2)*W, (cy-h/2)*H
    d.rectangle([x1,y1,(cx+w/2)*W,(cy+h/2)*H], outline=(255,165,0) if hard else (255,40,40), width=3)
    d.text((x1+3,y1+3), f"L{i}", fill=(255,255,0), font=font)
im.save(out); print(out, len([l for l in lines if l.strip()]), "boxes")
