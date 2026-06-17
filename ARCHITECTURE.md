# Architecture du moteur d'échecs

## Vue d'ensemble

Moteur d'échecs modulaire en Python s'appuyant sur `python-chess` pour les règles
et la représentation du plateau. Le projet a été construit par étapes progressives,
chaque étape ajoutant une couche sans modifier les précédentes.

```
chessbot/
├── gui.py           # Interface graphique pygame (point d'entrée principal)
├── main.py          # Point d'entrée unifié → lance gui.main()
├── engine.py        # Recherche du meilleur coup (algorithme)
├── evaluation.py    # Estimation de la valeur d'une position
├── Jouer.bat        # Lanceur Windows sans fenêtre terminal (double-clic)
├── requirements.txt
└── ARCHITECTURE.md  (ce fichier)
```

---

## Étapes de développement

### Étape 1 — Moteur de base : évaluation + Negamax (`evaluation.py`, `engine.py`)

**Ce qui a été fait :**
- `evaluation.py` : fonction `evaluate(board, level)` retournant un score en
  **centipions** (1 pion = 100 pts) du point de vue des Blancs.

  | Niveau | Évaluation |
  |--------|------------|
  | 1 | Toujours 0 → coups aléatoires |
  | 2 | Décompte matériel brut |
  | 3 | Matériel + piece-square tables (PST) |

  Les **PST** sont des matrices 8×8 donnant un bonus/malus selon la case occupée
  (ex : cavalier au centre = +30, cavalier en bord = −50).

  **Valeurs des pièces :**
  ```
  Pion=100  Cavalier=320  Fou=330  Tour=500  Dame=900  Roi=20000
  ```

- `engine.py` : algorithme **Negamax avec élagage Alpha-Bêta** pour les niveaux 1–3.

  ```
  Negamax(position, profondeur, α, β)
    └── best = max sur coups de  −Negamax(enfant, prof−1, −β, −α)
  ```

  Negamax unifie Minimax : le score est toujours du point de vue du joueur actif,
  donc `score_parent = −score_enfant`, ce qui évite deux branches max/min séparées.

---

### Étape 2 — Niveaux forts 4 et 5 (`engine.py`)

**Ce qui a été ajouté :**

- **Structure de pions** dans `evaluation.py` (niveaux 4+) :
  - Pénalité pions doublés : −20 centipions par pion supplémentaire sur la même colonne.
  - Pénalité pions isolés  : −15 centipions par pion sans voisin sur les colonnes adjacentes.

- **Tri des coups MVV-LVA** (*Most Valuable Victim, Least Valuable Attacker*) :
  on explore d'abord les captures de pièces précieuses par des pièces bon marché.
  Maximise les coupures alpha-bêta, permettant d'explorer quasi deux fois plus
  profond dans le même temps.

- **Quiescence search** : à la profondeur 0, on continue sur les captures (max 2 plies
  supplémentaires) jusqu'à une position calme, pour éviter l'effet d'horizon.

- **Table de transposition (TT)** (niveau 5) : `{hash_zobrist → (profondeur, score, flag)}`.
  Réutilise les positions déjà évaluées à profondeur ≥ actuelle.
  Flags : `exact` (valeur PV), `lower` (coupure bêta), `upper` (échec du nœud).

- **Deepening itératif avec budget temps** (niveaux 4–5) :
  ```
  pour d = 1, 2, 3, … jusqu'à depth_max ou expiration du budget :
      résultat = recherche_à_profondeur(d)
      si complet → meilleur_coup = résultat
  retourner meilleur_coup   # résultat de la dernière profondeur complète
  ```
  On garde uniquement le dernier résultat **complet** : un résultat interrompu
  à mi-profondeur est biaisé (seuls certains coups ont été évalués).

  Vérification du temps toutes les **2048 nœuds** (masque `& 0x7FF`) pour
  minimiser l'overhead de `time.perf_counter()`.

  | Niveau | Prof. max | Budget temps | Tri coups | Quiescence | TT |
  |--------|-----------|-------------|-----------|-----------|-----|
  | 4 | 4 | 1 s/coup | MVV-LVA | ✓ (2 plies) | — |
  | 5 | 5 | 2.5 s/coup | MVV-LVA | ✓ (2 plies) | ✓ |

---

### Étape 3 — Interface graphique initiale (`gui.py`)

**Ce qui a été fait :**
- Fenêtre **pygame** 800×640 avec plateau cliquable (glyphes Unicode ♔♕♖…).
- Deux clics pour jouer : 1er clic = sélectionne, 2e clic = joue.
- Points verts semi-transparents sur les cases légales de la pièce sélectionnée.
- Surbrillance du dernier coup (couleur olive).
- **Promotion automatique en dame** (cas le plus courant).
- Panneau latéral : niveau, tour, message.
- Touche `R` pour recommencer sans relancer le programme.

---

### Étape 4 — Moteur dans un thread séparé (`gui.py`)

**Problème résolu :**
Le calcul du moteur bloquait la boucle pygame → la fenêtre se figeait pendant
la réflexion.

**Solution :**
Le moteur tourne dans un `threading.Thread` daemon. Le thread principal pygame
continue de gérer les événements et d'afficher une animation "réfléchit…".
Le plateau est copié (`board.copy()`) avant d'être passé au thread pour éviter
toute contention sur l'état partagé.

```python
_fil = threading.Thread(
    target=lambda b=board_copie: _resultat.__setitem__(0, engine.best_move(b, niveau)),
    daemon=True,
)
_fil.start()
# ... boucle pygame continue ...
if not _fil.is_alive():   # résultat prêt → appliquer le coup
```

---

### Étape 5 — Optimisation des temps de réflexion (`engine.py`)

**Problème résolu :**
Les budgets initiaux (niveau 4 : 3 s, niveau 5 : 7 s) rendaient le jeu trop lent.

**Changements :**
- Budget niveau 4 : 3 s → **1 s**
- Budget niveau 5 : 7 s → **2,5 s**
- Profondeur quiescence : 3 plies → **2 plies**

Le deepening itératif garantit que le moteur retourne toujours un coup valide
même si le budget expire en cours de route.

---

### Étape 6 — Refonte visuelle complète (`gui.py`)

**Ce qui a été refait :**

- **Palette dark mode** inspirée chess.com :
  - Fond général `(22, 21, 18)`, cases claires `(238, 238, 210)`, cases sombres `(118, 150, 86)`.
  - Panneau latéral `(30, 29, 26)` séparé par une ligne fine.

- **Cadre et marges autour du plateau** (`MARGE = 28 px`) :
  - Les coordonnées (a–h, 1–8) sont affichées dans cette marge, comme sur un vrai échiquier.

- **Indicateurs de coups légaux améliorés** :
  - Case vide → petit cercle noir semi-transparent au centre.
  - Case adverse (capture) → anneau semi-transparent sur toute la case.

- **Surbrillance échec** : case du roi en rouge `(200, 40, 40)` quand il est en échec.

- **Pièces capturées** : affichées avec leurs glyphes dans le panneau, triées par valeur,
  avec le total matériel `+N` affiché en vert.

- **Avantage matériel** calculé en temps réel (Blancs/Noirs +N ou "Matériel égal").

- **Chronomètre live** : pendant la réflexion de l'IA, le temps écoulé s'affiche et
  s'incrémente à chaque frame.

- **Menu amélioré** : fond sombre, effets de survol (highlight vert + fond plus clair)
  à la souris.

- **Premier coup automatique** : si le joueur choisit les Noirs, l'IA (Blancs) joue
  son premier coup immédiatement sans attendre d'interaction.

---

### Étape 7 — Point d'entrée unifié (`main.py`, `Jouer.bat`)

**Ce qui a été fait :**
- `main.py` réduit à 4 lignes : il importe et appelle `gui.main()`.
  Utilisable depuis d'autres projets Python avec `from gui import main; main()`.
- `Jouer.bat` : lanceur Windows qui utilise `venv\Scripts\pythonw.exe` (pas de
  fenêtre terminal) pour un double-clic propre depuis l'explorateur de fichiers.

---

## Conventions générales

- Score toujours du **point de vue des Blancs** dans `evaluation.py` ;
  negamax inverse via `sign = 1 if board.turn == WHITE else -1`.
- **Centipions** comme unité universelle pour faciliter les comparaisons.
- `engine.py` et `evaluation.py` n'importent pas pygame : la séparation
  moteur / affichage est totale.
- Toute modification de l'évaluation ou des seuils de temps doit être
  documentée dans ce fichier.
