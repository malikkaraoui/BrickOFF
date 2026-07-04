# CH-8 — UI/UX complète (liquid glass)

> Durée : 2–3 semaines. Dépend de CH-5/6/7 (écrans fonctionnels existants à habiller).

---

## Direction artistique (cadrage)

- **Style** : liquid glass / translucidité, dans l'esprit du design system iOS récent — matériaux natifs (`.ultraThinMaterial`, etc.) plutôt que reproductions custom
- **Principes** : orienté usage, pas concept. Hiérarchie claire, geste minimal pour l'action principale (scanner)
- **Couleur** : palette neutre + accents tirés des couleurs LEGO vives (rouge/jaune/bleu) en touches, jamais en aplats massifs
- ⚠️ Ne pas imiter l'identité visuelle LEGO (logo, typographie maison, packaging) — contrainte légale CH-0

---

## Jalon 8.1 — Design system

### Tâches
1. `DesignSystem/Tokens.swift` : couleurs sémantiques (light/dark), typographie (échelle Dynamic Type), espacements (grille 4pt), rayons, ombres
2. Composants de base : `GlassCard`, `PrimaryButton`, `ColorDot` (pastille couleur LEGO), `CoverageBadge`, `EmptyStateView`, `PieceRow`
3. Catalogue de composants : un écran debug caché listant tous les composants dans tous leurs états

### Critères d'acceptation
- [ ] Tous les composants supportent dark mode + Dynamic Type (test aux 2 extrêmes de taille)
- [ ] Aucune couleur/espacement hardcodé hors Tokens dans les Features

---

## Jalon 8.2 — Écran Scan (habillage)

1. Preview plein écran, overlay bboxes animées (apparition douce, pas de clignotement — lisser les positions entre frames)
2. Bouton scanner central proéminent ; pendant la capture 5 frames : anneau de progression + consigne "Ne bougez pas"
3. Aides contextuelles : hint "Étalez les pièces" au premier scan (coachmark, désactivable)
4. Transition vers l'écran de revue : continuité visuelle (la capture figée reste, les overlays se figent)
5. Écran de revue : cartes glass par pièce, corrections en bottom sheet

### Critères d'acceptation
- [ ] Parcours scan complet sans lecture de doc par un utilisateur naïf (test sur 2 personnes)
- [ ] 60 fps maintenu sur le preview avec overlays (Instruments)

---

## Jalon 8.3 — Écrans Inventaire & Constructions (habillage)

1. Inventaire : sections par catégorie avec headers glass collants, stepper quantité élégant, swipe-to-delete, recherche dans la barre de navigation
2. Constructions : grille de cartes sets, coverage en anneau de progression, filtres par thème (chips), toggle strict/souple intégré et expliqué (tooltip)
3. Détail set : hero header, liste pièces manquantes mise en avant ("il vous manque 4 pièces")
4. États vides illustrés (illustrations simples maison, pas de visuels LEGO officiels)

### Critères d'acceptation
- [ ] Scroll fluide inventaire 1000+ lignes conservé après habillage
- [ ] Tous les états vides/erreur designés (pas de blanc)

---

## Jalon 8.4 — Onboarding & Settings

1. Onboarding 3 écrans max : promesse / comment scanner (étaler !) / permission caméra
2. Settings : mode matching par défaut, gestion inventaire (export JSON, vider), à propos (mentions légales, disclaimer "non affilié au groupe LEGO", attribution Rebrickable selon CH-0), version app + version catalogue + version modèles
3. Export inventaire : fichier JSON partageable (share sheet) — format documenté dans `12_CONVENTIONS_AI.md`

### Critères d'acceptation
- [ ] Disclaimer légal présent et conforme à `legal/BRAND_COMPLIANCE.md`
- [ ] Export JSON ré-importable (test aller-retour)

---

## Jalon 8.5 — Accessibilité & localisation

1. VoiceOver : tous les éléments interactifs labellisés, ordre de lecture cohérent sur l'écran de revue
2. Dynamic Type jusqu'à XXL sans casse de layout
3. Localisation : FR + EN (String Catalogs), zéro chaîne hardcodée
4. Contrastes : vérifier les textes sur matériaux glass (piège classique du style) — ajouter un fond de renfort si contraste < 4.5:1

### Critères d'acceptation
- [ ] Audit Accessibility Inspector sans erreur critique
- [ ] App 100% navigable en VoiceOver sur le parcours principal
- [ ] FR/EN complets

---

## Sortie de chantier CH-8

- App visuellement finale, accessible, FR/EN
- `CHANGELOG_CH8.md` + screenshots de chaque écran archivés
