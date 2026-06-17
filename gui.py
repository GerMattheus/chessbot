import sys
import pygame
import chess
import engine

# ── Constantes visuelles ──────────────────────────────────────────────────────
TAILLE_CASE = 80
TAILLE_PLATEAU = TAILLE_CASE * 8
MARGE_INFO = 160                          # panneau latéral droit
LARGEUR = TAILLE_PLATEAU + MARGE_INFO
HAUTEUR = TAILLE_PLATEAU

COULEUR_CASE_CLAIRE  = (240, 217, 181)
COULEUR_CASE_SOMBRE  = (181, 136,  99)
COULEUR_SELECTION    = (247, 247, 105, 180)   # jaune semi-transparent
COULEUR_COUP_LEGAL   = ( 20, 200,  20,  90)   # vert semi-transparent
COULEUR_FOND_INFO    = ( 40,  40,  40)
COULEUR_TEXTE        = (240, 240, 240)
COULEUR_DERNIERE_CASE= (205, 210,  60, 130)   # olive pour le dernier coup

# Unicode des pièces : (couleur, type) → glyphe
GLYPHES = {
    (chess.WHITE, chess.KING):   "♔",
    (chess.WHITE, chess.QUEEN):  "♕",
    (chess.WHITE, chess.ROOK):   "♖",
    (chess.WHITE, chess.BISHOP): "♗",
    (chess.WHITE, chess.KNIGHT): "♘",
    (chess.WHITE, chess.PAWN):   "♙",
    (chess.BLACK, chess.KING):   "♚",
    (chess.BLACK, chess.QUEEN):  "♛",
    (chess.BLACK, chess.ROOK):   "♜",
    (chess.BLACK, chess.BISHOP): "♝",
    (chess.BLACK, chess.KNIGHT): "♞",
    (chess.BLACK, chess.PAWN):   "♟",
}


# ── Utilitaires de conversion coordonnées ─────────────────────────────────────

def case_vers_pixel(case: int, joueur_color: chess.Color) -> tuple[int, int]:
    """Retourne le coin supérieur gauche (px) d'une case, orienté vers le joueur."""
    col = chess.square_file(case)
    rang = chess.square_rank(case)
    if joueur_color == chess.WHITE:
        rang = 7 - rang          # retourne le plateau pour les Blancs (rang 8 en haut)
    return col * TAILLE_CASE, rang * TAILLE_CASE


def pixel_vers_case(x: int, y: int, joueur_color: chess.Color) -> int | None:
    """Convertit un clic pixel en case chess, ou None si hors plateau."""
    if x < 0 or x >= TAILLE_PLATEAU or y < 0 or y >= HAUTEUR:
        return None
    col = x // TAILLE_CASE
    rang = y // TAILLE_CASE
    if joueur_color == chess.WHITE:
        rang = 7 - rang
    return chess.square(col, rang)


# ── Rendu ─────────────────────────────────────────────────────────────────────

def dessiner_plateau(surface: pygame.Surface, board: chess.Board,
                     selection: int | None, joueur_color: chess.Color,
                     dernier_coup: chess.Move | None) -> None:
    """Dessine les cases, les surbrillances et les pièces."""
    overlay = pygame.Surface((TAILLE_CASE, TAILLE_CASE), pygame.SRCALPHA)

    coups_legaux = set()
    if selection is not None:
        coups_legaux = {m.to_square for m in board.legal_moves
                        if m.from_square == selection}

    for case in chess.SQUARES:
        col = chess.square_file(case)
        rang = chess.square_rank(case)
        px, py = case_vers_pixel(case, joueur_color)
        couleur = COULEUR_CASE_CLAIRE if (col + rang) % 2 == 0 else COULEUR_CASE_SOMBRE
        pygame.draw.rect(surface, couleur, (px, py, TAILLE_CASE, TAILLE_CASE))

        # Surbrillance dernier coup
        if dernier_coup and case in (dernier_coup.from_square, dernier_coup.to_square):
            overlay.fill(COULEUR_DERNIERE_CASE)
            surface.blit(overlay, (px, py))

        # Surbrillance case sélectionnée
        if case == selection:
            overlay.fill(COULEUR_SELECTION)
            surface.blit(overlay, (px, py))

        # Points verts sur les cases cibles légales
        if case in coups_legaux:
            overlay.fill(COULEUR_COUP_LEGAL)
            surface.blit(overlay, (px, py))

    # Pièces
    for case, piece in board.piece_map().items():
        glyphe = GLYPHES[(piece.color, piece.piece_type)]
        px, py = case_vers_pixel(case, joueur_color)
        # Ombre légère pour la lisibilité
        ombre = FONTE_PIECE.render(glyphe, True, (30, 30, 30))
        surface.blit(ombre, (px + TAILLE_CASE // 2 - ombre.get_width() // 2 + 2,
                             py + TAILLE_CASE // 2 - ombre.get_height() // 2 + 2))
        texte = FONTE_PIECE.render(glyphe, True, (255, 255, 255) if piece.color == chess.WHITE else (10, 10, 10))
        surface.blit(texte, (px + TAILLE_CASE // 2 - texte.get_width() // 2,
                             py + TAILLE_CASE // 2 - texte.get_height() // 2))

    # Coordonnées (a-h, 1-8)
    for i in range(8):
        lettre = FONTE_COORD.render(chr(ord('a') + i), True, (100, 100, 100))
        surface.blit(lettre, (i * TAILLE_CASE + 4, HAUTEUR - 16))
        chiffre = FONTE_COORD.render(str(8 - i if joueur_color == chess.WHITE else i + 1),
                                     True, (100, 100, 100))
        surface.blit(chiffre, (4, i * TAILLE_CASE + 4))


def dessiner_panneau(surface: pygame.Surface, board: chess.Board,
                     niveau: int, joueur_color: chess.Color, message: str) -> None:
    """Dessine le panneau latéral : niveau, tour, message."""
    pygame.draw.rect(surface, COULEUR_FOND_INFO,
                     (TAILLE_PLATEAU, 0, MARGE_INFO, HAUTEUR))

    lignes = [
        f"Niveau {niveau}",
        "",
        f"Tour : {'Blancs' if board.turn == chess.WHITE else 'Noirs'}",
        f"Vous : {'Blancs' if joueur_color == chess.WHITE else 'Noirs'}",
        "",
        message,
    ]
    y = 20
    for ligne in lignes:
        rendu = FONTE_INFO.render(ligne, True, COULEUR_TEXTE)
        surface.blit(rendu, (TAILLE_PLATEAU + 10, y))
        y += 28


# ── Boucle principale ─────────────────────────────────────────────────────────

def choisir(ecran: pygame.Surface, titre: str, options: list[str]) -> int:
    """Menu de sélection simple affiché dans la fenêtre pygame."""
    clock = pygame.time.Clock()
    while True:
        ecran.fill((30, 30, 30))
        t = FONTE_INFO.render(titre, True, COULEUR_TEXTE)
        ecran.blit(t, (LARGEUR // 2 - t.get_width() // 2, 80))
        rects = []
        for i, opt in enumerate(options):
            y = 160 + i * 60
            rect = pygame.Rect(LARGEUR // 2 - 120, y, 240, 44)
            pygame.draw.rect(ecran, (70, 70, 70), rect, border_radius=6)
            label = FONTE_INFO.render(f"{i + 1}. {opt}", True, COULEUR_TEXTE)
            ecran.blit(label, (rect.x + 12, rect.y + 10))
            rects.append(rect)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        return i + 1
            if event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_3:
                choix = event.key - pygame.K_0
                if 1 <= choix <= len(options):
                    return choix
        clock.tick(30)


def main() -> None:
    pygame.init()
    ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
    pygame.display.set_caption("Moteur d'échecs Python")
    clock = pygame.time.Clock()

    # Fontes déclarées en global pour être accessibles dans les fonctions de rendu
    global FONTE_PIECE, FONTE_INFO, FONTE_COORD
    # Cherche une fonte système supportant les glyphes Unicode d'échecs
    for nom in ("Segoe UI Symbol", "DejaVu Sans", "Arial Unicode MS", "FreeSans", None):
        FONTE_PIECE  = pygame.font.SysFont(nom, 56)
        FONTE_INFO   = pygame.font.SysFont(nom, 20)
        FONTE_COORD  = pygame.font.SysFont(nom, 14)
        if FONTE_PIECE.render("♔", True, (0, 0, 0)).get_width() > 4:
            break  # fonte valide trouvée

    # Menus de démarrage
    niveau      = choisir(ecran, "Choisissez un niveau :",
                          ["Débutant (aléatoire)", "Intermédiaire (matériel)", "Avancé (positionnel)"])
    couleur_idx = choisir(ecran, "Jouez avec quelle couleur ?", ["Blancs", "Noirs"])
    joueur_color = chess.WHITE if couleur_idx == 1 else chess.BLACK

    board = chess.Board()
    selection: int | None = None
    dernier_coup: chess.Move | None = None
    message = "À vous de jouer !"
    moteur_en_cours = False

    while True:
        # ── Événements ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                # R → recommencer
                main()
                return

            if (event.type == pygame.MOUSEBUTTONDOWN
                    and not board.is_game_over()
                    and board.turn == joueur_color
                    and not moteur_en_cours):

                case_cliquee = pixel_vers_case(event.pos[0], event.pos[1], joueur_color)
                if case_cliquee is None:
                    selection = None
                elif selection is None:
                    # Premier clic : sélectionne la pièce si elle appartient au joueur
                    piece = board.piece_at(case_cliquee)
                    if piece and piece.color == joueur_color:
                        selection = case_cliquee
                else:
                    # Deuxième clic : tente de jouer le coup
                    coup = chess.Move(selection, case_cliquee)
                    # Promotion automatique en dame
                    if (board.piece_at(selection) and
                            board.piece_at(selection).piece_type == chess.PAWN and
                            chess.square_rank(case_cliquee) in (0, 7)):
                        coup = chess.Move(selection, case_cliquee, promotion=chess.QUEEN)

                    if coup in board.legal_moves:
                        board.push(coup)
                        dernier_coup = coup
                        selection = None
                        message = "Moteur réfléchit…"
                        moteur_en_cours = True
                    else:
                        # Re-sélectionne si on clique une autre pièce alliée
                        piece = board.piece_at(case_cliquee)
                        selection = case_cliquee if (piece and piece.color == joueur_color) else None

        # ── Tour du moteur (hors boucle d'événements pour ne pas bloquer) ─────
        if moteur_en_cours and not board.is_game_over():
            coup_moteur = engine.best_move(board, niveau)
            if coup_moteur:
                board.push(coup_moteur)
                dernier_coup = coup_moteur
            message = "À vous de jouer !"
            moteur_en_cours = False

        # ── Message de fin de partie ───────────────────────────────────────────
        if board.is_game_over():
            outcome = board.outcome()
            if outcome and outcome.winner is not None:
                gagnant = "Blancs" if outcome.winner == chess.WHITE else "Noirs"
                message = f"{gagnant} gagnent ! (R = rejouer)"
            else:
                message = f"Match nul ({board.result()})  R = rejouer"

        # ── Rendu ─────────────────────────────────────────────────────────────
        dessiner_plateau(ecran, board, selection, joueur_color, dernier_coup)
        dessiner_panneau(ecran, board, niveau, joueur_color, message)
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
