"""Planches de contrôle : rouge=pièce comptable, orange=hard, BLEU=coupée par le cadre.
Compteur en haut-droite = nb de pièces comptables (ni hard ni coupées).
Troncature = règle géométrique : boîte dont un côté touche le bord (< EPS)."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path("data/processed/realworld_piles/decision")
EPS = 0.012  # ~1.2% du côté = bord de cadre
counts_file = root.parent / "piece_counts.json"
gt_counts = json.load(open(counts_file)) if counts_file.exists() else {}

def parse(name):
    boxes = []
    for line in (root/"labels"/(name.stem+".txt")).read_text().splitlines():
        if not line.strip(): continue
        hard = line.startswith("# hard")
        _, cx, cy, w, h = map(float, line.replace("# hard ","").split())
        x1,y1,x2,y2 = cx-w/2, cy-h/2, cx+w/2, cy+h/2
        trunc = x1 <= EPS or y1 <= EPS or x2 >= 1-EPS or y2 >= 1-EPS
        boxes.append((x1,y1,x2,y2,hard,trunc))
    return boxes

imgs = sorted((root/"images").iterdir())
tot_trunc = 0
for si in range(2):
    tiles=[]
    for p in imgs[si*25:(si+1)*25]:
        im=Image.open(p).convert("RGB"); d=ImageDraw.Draw(im); W,H=im.size
        countable=0
        for x1,y1,x2,y2,hard,trunc in parse(p):
            col=(0,120,255) if trunc else ((255,165,0) if hard else (255,40,40))
            d.rectangle([x1*W,y1*H,x2*W,y2*H],outline=col,width=max(5,W//220))
            if not hard and not trunc: countable+=1
            if trunc: 
                pass
        tot_trunc += sum(1 for b in parse(p) if b[5])
        im.thumbnail((520,520)); dd=ImageDraw.Draw(im); w2,h2=im.size
        try: f=ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",34)
        except: f=ImageFont.load_default()
        num=p.stem.split("IMG_")[1]
        gtc=gt_counts.get(p.name)
        lab=f"{num}: {countable}p" + (f"/{gtc}" if gtc else "")
        dd.rectangle([0,0,len(lab)*20+10,42],fill=(0,0,0)); dd.text((5,4),lab,fill=(255,255,0),font=f)
        tiles.append(im)
    tw=max(t.width for t in tiles);th=max(t.height for t in tiles)
    sh=Image.new("RGB",(5*tw,5*th),(10,10,10))
    for i,t in enumerate(tiles): sh.paste(t,((i%5)*tw,(i//5)*th))
    sh.save(f"ml/verif_v2_{si+1}.png")
print(f"planches ok | pièces coupées (bleu) détectées géométriquement : {tot_trunc//2}")
