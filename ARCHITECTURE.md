# Architecture du moteur d'échecs

## Vue d'ensemble

Moteur d'échecs modulaire en Python s'appuyant sur `python-chess` pour les règles
et la représentation du plateau. Le projet est découpé en trois modules à
responsabilité unique, facilitant la montée en compétence progressive.

```
chessbot/
├── gui.py           # Interface graphique pygame (point d'entrée jouable)
├── main.py          # Boucle de jeu terminal (fallback sans GUI)
├── engine.py        # Recherche du meilleur coup (algorithme)
├── evaluation.py    # Estimation de la valeur d'une position
├── requirements.txt
└── ARCHITECTURE.md  (ce fichier)
```

---

## Modules

### `evaluation.py` — Évaluation statique d'une position

**Pourquoi ?**
Séparer l'évaluation de la recherche permet de changer la « vue » du moteur sur
la position sans toucher à l'algorithme de recherche. C'est aussi ici que se
définissent les niveaux de jeu.

**Comment ?**
La fonction centrale `evaluate(board, level)` retourne un score en **centipions**
(1 pion = 100 pts) du point de vue des Blancs :

| Niveau | Fonctionnalités d'évaluation |
|--------|------------------------------|
| 1 | Score = 0 → coups aléatoires |
| 2 | Décompte matériel brut |
| 3 | Matériel + tables de positions (PST) |
| 4 | Matériel + PST + structure de pions |
| 5 | Identique niveau 4 (force = algorithme) |

**Valeurs des pièces (centipions) :**
```
Pion=100  Cavalier=320  Fou=330  Tour=500  Dame=900  Roi=20000
```

Les **piece-square tables** (niveau 3+) sont des matrices 8×8 qui donnent un
bonus/malus selon la case occupée par une pièce (ex : cavalier au centre = bonus).

La **structure de pions** (niveau 4+) ajoute :
- Pénalité pions doublés : -20 centipions par pion supplémentaire sur la même colonne.
- Pénalité pions isolés  : -15 centipions par pion sans voisin sur les colonnes adjacentes.

---

### `engine.py` — Recherche du meilleur coup

**Pourquoi ?**
Isoler la recherche permet de brancher n'importe quelle fonction d'évaluation
sans changer le moteur de recherche lui-même.

**Comment ?**
Algorithme **Negamax avec élagage Alpha-Bêta** :

```
Negamax(position, profondeur, α, β)
  ├── Si feuille → quiescence(α, β)   [niveaux 4-5]  ou evaluate()
  └── best = max sur coups de  -Negamax(enfant, prof-1, -β, -α)
```

Negamax est une simplification de Minimax : le score est toujours du point
de vue du joueur actif, donc `score_parent = -score_enfant`. Cela évite
d'avoir deux branches max/min séparées.

**Fonctionnalités cumulatives par niveau :**

| Niveau | Prof. | Évaluation | Tri des coups | Quiescence | Table de transposition |
|--------|-------|-----------|--------------|-----------|----------------------|
| 1 | — | aucune | — | — | — |
| 2 | 2 | matériel | — | — | — |
| 3 | 3 | matériel + PST | — | — | — |
| 4 | 4 | matériel + PST + structure | MVV-LVA | ✓ | — |
| 5 | 5 | idem niveau 4 | MVV-LVA | ✓ | ✓ |

**Tri des coups (MVV-LVA)** — *Most Valuable Victim, Least Valuable Attacker* :
on examine d'abord les captures de pièces précieuses par des pièces bon marché.
Ça maximise les coupures alpha-bêta et permet d'explorer quasi deux fois plus profond.

**Quiescence search** : quand on atteint la profondeur 0, au lieu d'évaluer
immédiatement, on continue à explorer uniquement les captures jusqu'à une
position « calme ». Sans ça, le moteur peut croire qu'une position est bonne
juste avant que l'adversaire prenne une pièce (effet d'horizon).

**Table de transposition (TT)** : dictionnaire `{hash_zobrist → (profondeur, score, flag)}`.
Quand une position a déjà été évaluée à une profondeur ≥ actuelle, on réutilise
le résultat au lieu de re-chercher. Les flags indiquent si le score est exact,
une borne inférieure (coupure bêta) ou supérieure (échec du nœud).

---

### `main.py` — Interface et boucle de jeu

**Pourquoi ?**
Point d'entrée unique qui orchestre les autres modules sans contenir de logique
métier.

**Comment ?**
1. L'utilisateur choisit sa couleur et le niveau du moteur.
2. La boucle principale alterne coups humains (saisie UCI, ex : `e2e4`) et
   coups du moteur (appel à `engine.best_move()`).
3. Affichage du plateau ASCII via `python-chess` après chaque coup.

---

---

### `gui.py` — Interface graphique (pygame)

**Pourquoi ?**
`main.py` exige de connaître la notation UCI (ex: `e2e4`), ce qui n'est pas
jouable en pratique. `gui.py` ajoute une fenêtre avec un plateau cliquable,
sans toucher à `engine.py` ni `evaluation.py`.

**Comment ?**
Le fichier est organisé en trois couches :

1. **Conversion coordonnées** (`case_vers_pixel`, `pixel_vers_case`)  
   Traduit entre les cases `python-chess` (entiers 0–63) et les pixels pygame.
   Le plateau est orienté selon la couleur du joueur (Blancs en bas).

2. **Rendu** (`dessiner_plateau`, `dessiner_panneau`)  
   - Cases colorées + surbrillance du dernier coup (olive) et de la sélection (jaune).  
   - Points verts semi-transparents sur les **cases légales** de la pièce sélectionnée.  
   - Pièces en glyphes Unicode (♔♕♖…) avec ombre pour la lisibilité.  
   - Panneau latéral : niveau, tour, messages.

3. **Boucle principale** (`main`)  
   - Deux clics pour jouer : 1er clic = sélectionne une pièce, 2e clic = joue le coup.  
   - **Promotion automatique en dame** (cas le plus courant).  
   - Le coup du moteur est calculé dans la même boucle, juste après le coup humain,  
     de façon synchrone (le rendu se fige brièvement sur "Moteur réfléchit…").  
   - `R` permet de recommencer une partie sans relancer le programme.

**Lancer la GUI :**
```bash
pip install pygame python-chess
python gui.py
```

---

## Conventions

- Score toujours du **point de vue des Blancs** ; le Minimax inverse selon
  `board.turn`.
- Centipions comme unité universelle pour faciliter les comparaisons.
- Chaque nouvelle fonctionnalité (élagage, ouvertures, etc.) doit être
  documentée dans ce fichier avant d'être codée.
