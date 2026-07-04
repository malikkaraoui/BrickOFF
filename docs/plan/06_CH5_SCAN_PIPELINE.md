# CH-5 — Pipeline scan (caméra + inférence + agrégation)

> Durée : 2–3 semaines. Dépend de CH-3 (mlpackages) + CH-4 (fondations).
> Cœur technique de l'app. À découper service par service, chacun testable isolément.

---

## Architecture cible

```
AVFoundation (CVPixelBuffer)
   │  (throttle: 1 frame analysée / ~500ms, pas chaque frame)
   ▼
DetectionService (CoreML DET) ──► [bbox]*
   ▼
pour chaque bbox:
   ├── ClassificationService (CoreML CLS) ──► partId + confidence
   └── ColorService (algo LAB Swift)      ──► colorId + confidence
   ▼
ScanAggregator (actor) ── déduplication multi-frames ──► [DetectedPiece]
   ▼
ScanViewModel ──► UI (overlay bboxes temps réel + liste pièces)
```

---

## Jalon 5.1 — Capture caméra

### Spécifications
1. `CameraService` : AVCaptureSession, sortie `AVCaptureVideoDataOutput` (CVPixelBuffer)
2. Résolution capture : 1920×1080 (downscale vers 640×640 pour DET fait par CoreML/Vision)
3. Throttling : ne soumettre une frame à l'inférence que si la précédente est terminée ET ≥ 400ms écoulées (file d'attente de profondeur 1, on jette les frames intermédiaires)
4. Preview : `AVCaptureVideoPreviewLayer` wrappé SwiftUI
5. Gestion lifecycle : pause session quand la vue disparaît / app en background

### Critères d'acceptation
- [ ] Preview fluide 30+ fps indépendamment de l'inférence
- [ ] Aucune frame en attente ne s'accumule (vérifier mémoire stable sur 5 min)
- [ ] Session correctement stoppée/relancée sur background/foreground

---

## Jalon 5.2 — DetectionService

### Spécifications
1. Charge `DetModel.mlpackage` une fois (lazy, au premier scan)
2. Input : CVPixelBuffer → via Vision (`VNCoreMLRequest`) — Vision gère resize + orientation
3. ⚠️ Orientation : mapper correctement `CGImagePropertyOrientation` depuis l'orientation device — bug classique (boxes décalées de 90°)
4. Output : `[RawDetection]` = bbox normalisée + score, seuil de confiance configurable (départ 0.35), NMS selon décision CH-3
5. Service = actor ou classe thread-safe ; inférence hors main thread

### Tests
- Test unitaire avec 5 images bundle de référence : nombre de détections attendu ±1, IoU vs annotations ≥ 0.8

### Critères d'acceptation
- [ ] Boxes correctes dans les 4 orientations device
- [ ] Latence conforme au benchmark CH-3 (± 20%)
- [ ] Tests unitaires verts

---

## Jalon 5.3 — ClassificationService

### Spécifications
1. Charge `ClsModel.mlpackage`
2. Input : crop de la bbox depuis le pixel buffer pleine résolution (PAS depuis le 640×640 — qualité supérieure), avec padding de 10% autour de la bbox
3. Output : `(partId: String, confidence: Double, top5: [(String, Double)])`
4. Mapping index → partId via `classes_v1.json` embarqué (charger une fois, vérifier version)
5. Batching : si > 10 crops, traiter par lots pour limiter les allers-retours

### Tests
- 20 crops de référence bundle → top-1 attendu ≥ 18/20

### Critères d'acceptation
- [ ] Mapping classes vérifié (test : index 0, index 999, 3 indices médians)
- [ ] Tests verts, latence conforme

---

## Jalon 5.4 — ColorService (port Swift de l'algo Python)

### Spécifications
1. Réimplémenter EXACTEMENT l'algo validé en CH-2 jalon 2.3 (mêmes étapes, mêmes seuils depuis le même JSON de config)
2. Conversion sRGB → LAB en Swift : implémenter la conversion standard (sRGB → XYZ D65 → LAB) — pas de lib externe nécessaire, ~40 lignes
3. Charger `lego_colors_lab.json`
4. **Test de parité obligatoire** : 50 crops de référence → comparer color_id Swift vs Python : ≥ 48/50 identiques, ΔE calculés à < 0.5 d'écart

### Critères d'acceptation
- [ ] Parité Python/Swift validée et documentée
- [ ] "unknown" retourné au-delà du seuil, jamais de couleur inventée

---

## Jalon 5.5 — ScanAggregator (multi-frames)

> Problème : l'utilisateur balaye la scène, les mêmes pièces sont détectées sur plusieurs frames, avec du bruit. Il faut consolider.

### Algorithme V1 (simple et suffisant)
1. Mode de scan : l'utilisateur cadre la scène, appuie sur "Scanner" → on capture **N = 5 frames consécutives analysées** (≈ 2,5 s), device tenu stable (afficher consigne)
2. Appariement inter-frames : deux détections de frames différentes sont la même pièce si IoU > 0.5
3. Pour chaque pièce consolidée :
   - partId = vote majoritaire pondéré par confidence sur les N occurrences
   - colorId = idem
   - confidence finale = moyenne des votes gagnants
4. Filtre final : rejeter toute pièce vue sur < 3 frames sur 5 (élimine les faux positifs transitoires)
5. Output : `[DetectedPiece]` consolidé → écran de revue

### Décision UX associée (figée)
Scan = action déclenchée (photo "longue"), PAS un flux continu qui remplit l'inventaire en live. Le live n'affiche que les bboxes en preview (feedback), l'ajout à l'inventaire passe par l'écran de revue.

### Critères d'acceptation
- [ ] Sur une scène test de 20 pièces : ≥ 18 pièces consolidées, ≤ 1 faux positif
- [ ] Implementé en actor, aucun data race (vérifier avec Thread Sanitizer)

---

## Jalon 5.6 — Écran de revue scan

### Spécifications
1. Après agrégation : capture figée + overlay des pièces détectées
2. Liste des pièces : vignette (crop), nom de pièce, couleur, quantité regroupée
3. Actions utilisateur : supprimer une détection erronée, corriger une couleur (picker palette), corriger une pièce (recherche dans les 1000 classes, pré-filtrée par top-5 du classifier)
4. Bouton "Ajouter à l'inventaire" → handoff CH-6
5. Pièces "unknown" (couleur ou classe incertaine) : affichées dans une section dédiée, jamais ajoutées silencieusement

### Critères d'acceptation
- [ ] Toutes les corrections fonctionnelles
- [ ] Top-5 proposé lors de la correction de pièce
- [ ] Aucun ajout à l'inventaire sans action explicite utilisateur

---

## Sortie de chantier CH-5

- Pipeline scan complet fonctionnel sur device, du déclenchement à l'écran de revue
- Tests unitaires par service + test de parité couleur
- `CHANGELOG_CH5.md` + vidéo de démo (capture écran) archivée
