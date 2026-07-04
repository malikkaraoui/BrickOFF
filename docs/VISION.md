# VISION — L'étoile du Nord de BrickOFF

> **Statut : NORMATIF — formulation du product owner (Malik), 2026-07-04.**
> Tout arbitrage, tout chantier, toute feature se juge à l'aune de ce document.

## La vision, en une phrase

**Je prends mon téléphone, je photographie ou filme mon tas de LEGO en vrac, je choisis ce que je
veux construire — un monument, une maison, une voiture — et l'app me génère un plan de construction
inédit, réalisable avec exactement les pièces que j'ai devant les yeux, puis me guide pas à pas
jusqu'au résultat, comme une notice LEGO officielle.**

Le cœur du produit : **recycler des LEGO en pagaille en constructions nouvelles** — donner une
seconde vie à des pièces orphelines, sans acheter quoi que ce soit.

## Les trois piliers non négociables

1. **100 % local.** Pas de serveur d'inférence : latence nulle, coût marginal nul, vie privée
   totale, fonctionne partout. C'est un choix économique (pas de coût cloud à couvrir) autant
   que produit.
2. **Multi-plateforme : iOS ET Android.** Le public visé (férus de LEGO, familles) est sur les
   deux. *Séquencement d'exécution : iOS d'abord (V1), Android ensuite (V2) — voir
   [D01](plan/ARBITRAGES/D01_PLATEFORME.md) : on prouve le produit sur un OS avant de doubler
   la surface.*
3. **Gratuit, financé par la publicité.** L'app doit vivre et rémunérer son auteur — voir
   [D03](plan/ARBITRAGES/D03_MONETISATION.md).

## Le chemin vers la vision (pourquoi on ne commence pas par la génération)

La vision finale — générer un plan *qui n'existe pas* — est le problème le plus dur du domaine
(génération sous contrainte d'inventaire + validation physique + guidage séquentiel). On y va
par paliers, chaque palier étant un produit utile en soi :

| Palier | Livrable | Ce que l'utilisateur peut faire |
|---|---|---|
| **V1** | Scan + inventaire + matching | "Voici les sets officiels que tu peux (presque) construire avec ton tas" |
| **V1.5** | Blueprints paramétriques + équivalences ([doc 13](plan/13_GENERATION_FIGURES.md) A1+A2) | "Choisis un canard, une voiture, une maison → plan adapté À TES pièces, avec étapes" — **première incarnation réelle de la vision** |
| **V2** | Android + extension du catalogue de blueprints (OTA) | Même produit, tout le monde |
| **V3** | Génération libre (A3, après spike Go/No-Go) | "Décris ce que tu veux → plan inédit" — la vision complète |

**Pourquoi ce séquencement** : chaque palier réutilise intégralement le précédent (le scan et
l'inventaire de V1 sont les fondations de tout), et le palier V1.5 délivre déjà l'expérience
"je choisis → on me guide pas à pas" avec un risque technique faible — la magie perçue ne
nécessite pas d'attendre la génération IA.

## Le guidage pas-à-pas (exigence transverse dès V1.5)

Les notices officielles LEGO sont la référence UX absolue (une étape = peu de pièces, vue 3D
stable, pièces de l'étape mises en évidence). Le format de nos blueprints doit intégrer les
étapes **dès la conception** (champ `steps` dans le JSON blueprint) — pas en post-traitement.
Une étude des formats d'instructions existants (notices LEGO, LDraw MPD/steps, BrickLink Studio)
est au backlog de recherche : `docs/research/INSTRUCTIONS_FORMATS.md`.

## Ce que cette vision interdit

- Toute dépendance serveur pour une fonction cœur (scan, matching, génération, guidage).
- Tout palier qui ne fonctionne pas en mode avion.
- Sacrifier la fiabilité du scan (fondation de tout) pour accélérer un palier supérieur.
