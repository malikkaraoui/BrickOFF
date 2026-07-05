# Protocole photos "set TAS" (S.0) — pour Malik 📸

> ~100 photos, 3-4 h au total, fractionnables. Ces photos sont **le juge** de tout le chantier
> synthétique : leur diversité vaut plus que leur beauté. Elles ne serviront JAMAIS à
> l'entraînement. Lire aussi : `data/manifests/annotation_convention.md` (ce qui sera annoté).

## Matériel
- Ton iPhone principal (réglages auto, pas de mode macro/portrait, pas de zoom > 1×).
- Pour le HOLDOUT : un 2e téléphone (iPad OK) OU un autre lieu (voir §Quotas).
- Tes LEGO en vrac. Varie les pièces entre scènes (re-mélange, change de boîte).

## La scène type
1. Verse **10 à 40 pièces** en vrac sur le fond choisi (laisse-les tomber naturellement,
   ne les arrange PAS — les chevauchements sont exactement ce qu'on veut).
2. 1 à 2 photos par tas (si 2 : change franchement d'angle), puis re-mélange/repioche.
3. Cadre le tas à ~30-80 % de l'image, netteté sur le tas, à main levée (le micro-flou
   naturel est bienvenu).

## Quotas à respecter (l'important est là)

| Axe | Répartition sur ~100 photos |
|---|---|
| **Éclairages** | ~1/3 lumière du jour · ~1/3 LED/plafonnier · **~1/3 lampe chaude/tamisée (le soir)** |
| **Fonds** | table bois · sol clair/carrelage · tapis/moquette · + 1-2 fonds libres (canapé, bureau encombré…) |
| **Angles** | ~60 % en plongée (au-dessus, 60-90°) · ~40 % de biais (30-60°) · hauteurs 25-60 cm |
| **Tailles de tas** | ~20 % petits (10-15 pièces) · ~40 % moyens (16-25) · ~40 % gros (26-40) |
| **Distracteurs** | sur ~1/4 des scènes, laisse traîner 1-3 objets non-LEGO (stylo, pièce de monnaie, câble, clé…) |
| **HOLDOUT 🔒** | **≥ 20 photos ailleurs que chez toi ET/OU avec le 2e téléphone** — dépose-les dans un sous-dossier séparé `holdout/` |

## Ce qu'on ÉVITE
- Pièces alignées/triées, tas "arrangés pour la photo".
- Toujours le même coin de la même table.
- Zoom numérique, flash forcé (1-2 photos flash = OK pour la diversité), mode portrait/bokeh.
- Doubles quasi identiques du même tas sous le même angle.

## Dépôt
```
data/raw/piles_malik/
├── session_01/   IMG_xxx.jpg …   (nomme les dossiers par session, peu importe le reste)
└── holdout/      IMG_xxx.jpg …   (les ≥ 20 photos hors-domicile / 2e téléphone)
```
Dis-le-moi quand c'est déposé : je lance le pilote d'annotation chronométré (5 scènes),
puis la baseline det_v1 sur ce set — c'est elle qui calibrera le critère de succès de l'It.3.
