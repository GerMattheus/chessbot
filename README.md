# ChessBot

Moteur d'échecs Python jouable avec une interface graphique pygame.  
Cinq niveaux de difficulté, de l'aléatoire complet jusqu'à un Negamax profondeur 5
avec quiescence search et table de transposition.

---

## Prérequis

- Python 3.10 ou supérieur
- Dépendances : `pygame` et `python-chess`

```bash
pip install pygame python-chess
```

Ou avec le fichier de dépendances du projet :

```bash
pip install -r requirements.txt
```

> Si le projet dispose d'un environnement virtuel (`venv/`), activez-le d'abord :
> ```bash
> # Windows
> venv\Scripts\activate
> # macOS / Linux
> source venv/bin/activate
> ```

---

## Lancement

### Option 1 — Double-clic (Windows)

Double-cliquez sur **`Jouer.bat`** dans le dossier du projet.  
La fenêtre de jeu s'ouvre sans terminal.

### Option 2 — Terminal

```bash
python main.py
# ou directement
python gui.py
```

### Option 3 — Depuis un autre projet Python

```python
from gui import main
main()
```

---

## Comment jouer

### 1. Choisir un niveau

Au lancement, un menu vous propose cinq niveaux :

| Niveau | Nom | Stratégie |
|--------|-----|-----------|
| 0 | Débutant | Coups entièrement aléatoires |
| 1 | Novice | Maximise l'avantage matériel, profondeur 2 |
| 2 | Facile | Matériel + tables de positions, profondeur 3 |
| 3 | Intermédiaire | + structure de pions + quiescence, ~1 s/coup |
| 4 | Fort | + table de transposition, ~2,5 s/coup |

Cliquez sur le niveau ou appuyez sur la touche **1** à **5**.

### 2. Choisir votre couleur

Cliquez sur **Blancs** ou **Noirs**.  
Si vous choisissez les Noirs, l'IA joue automatiquement le premier coup.

### 3. Jouer

- **1er clic** sur une de vos pièces → la sélectionne (surbrillance jaune).
  - Les cases légales s'affichent : **point noir** pour les déplacements, **anneau** pour les captures.
- **2e clic** sur une case légale → joue le coup.
- Cliquez sur une autre pièce alliée pour changer de sélection.

**Promotion** : un pion arrivant en dernière rangée est automatiquement promu en **dame**.

### 4. Pendant la réflexion de l'IA

Le panneau affiche "IA réfléchit…" avec le temps écoulé en temps réel.  
L'interface reste réactive — vous pouvez déplacer la fenêtre ou fermer le jeu.

### 5. Fin de partie

Quand la partie est terminée (mat, pat, nulle), le résultat apparaît dans le panneau.  
Appuyez sur **R** à tout moment pour recommencer une nouvelle partie.

---

## Panneau latéral

| Information | Description |
|-------------|-------------|
| Niveau X – Nom | Difficulté en cours et camp joué par l'IA |
| Tour : Blancs/Noirs | Qui doit jouer |
| Coup n° N | Numéro du coup actuel |
| IA réfléchit / À vous | Statut de la partie |
| IA : X.Xs | Temps pris par l'IA sur le dernier coup |
| Blancs/Noirs ont pris | Pièces capturées par chaque camp |
| Avantage | Avantage matériel en centipions |

---

## Structure du projet

```
chessbot/
├── gui.py           # Interface graphique pygame
├── main.py          # Point d'entrée (lance gui.main())
├── engine.py        # Algorithme Negamax + Alpha-Bêta
├── evaluation.py    # Évaluation statique des positions
├── Jouer.bat        # Lanceur Windows sans terminal
├── requirements.txt
└── ARCHITECTURE.md  # Documentation technique détaillée
```

Pour comprendre les choix algorithmiques et l'historique de développement,
consultez [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Raccourcis clavier

| Touche | Action |
|--------|--------|
| `R` | Nouvelle partie |
| `1`–`5` | Sélectionner dans les menus |

---

## Copyright

Copyright © 2025 GerMattheus

Ce projet est distribué sous licence **MIT**.

Permission est accordée, gratuitement, à toute personne obtenant une copie
de ce logiciel et des fichiers de documentation associés, de traiter le logiciel
sans restriction, notamment les droits d'utilisation, de copie, de modification,
de fusion, de publication, de distribution, de sous-licence et/ou de vente,
sous réserve des conditions suivantes :

> La notice de copyright ci-dessus et cette notice de permission doivent être
> incluses dans toutes les copies ou parties substantielles du logiciel.

LE LOGICIEL EST FOURNI "EN L'ÉTAT", SANS GARANTIE D'AUCUNE SORTE, EXPRESSE OU
IMPLICITE. EN AUCUN CAS LES AUTEURS OU TITULAIRES DU COPYRIGHT NE POURRONT ÊTRE
TENUS RESPONSABLES DE TOUT DOMMAGE RÉSULTANT DE L'UTILISATION DU LOGICIEL.
