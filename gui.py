import sys
import threading
import time
import pygame
import chess
import engine

# ── Constantes visuelles ──────────────────────────────────────────────────────
TAILLE_CASE    = 80
MARGE          = 28
TAILLE_PLATEAU = TAILLE_CASE * 8
PANNEAU_W      = 220
LARGEUR        = MARGE * 2 + TAILLE_PLATEAU + PANNEAU_W
HAUTEUR        = MARGE * 2 + TAILLE_PLATEAU

# Palette dark mode (inspiré chess.com)
C_FOND    = ( 22,  21,  18)
C_CADRE   = ( 58,  54,  48)
C_CLAIRE  = (238, 238, 210)
C_SOMBRE  = (118, 150,  86)
C_SELECT  = (247, 247, 105, 160)
C_DERNIER = (205, 210,  60, 100)
C_ECHEC   = (200,  40,  40, 180)
C_DOT     = (  0,   0,   0,  65)
C_PANNEAU = ( 30,  29,  26)
C_TEXTE   = (232, 230, 225)
C_DIM     = (130, 125, 118)
C_ACCENT  = (103, 182, 103)
C_SEP     = ( 55,  52,  48)
C_COORD   = (160, 155, 145)

NOM_NIVEAU = {1: "Débutant", 2: "Novice", 3: "Facile",
              4: "Intermédiaire", 5: "Fort"}

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

VALEUR = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
          chess.ROOK: 5, chess.QUEEN: 9}


# ── Utilitaires ───────────────────────────────────────────────────────────────

def piece_capturee(board: chess.Board, move: chess.Move) -> chess.Piece | None:
    if not board.is_capture(move):
        return None
    if board.is_en_passant(move):
        sq = chess.square(chess.square_file(move.to_square),
                          chess.square_rank(move.from_square))
        return board.piece_at(sq)
    return board.piece_at(move.to_square)


def case_vers_pixel(case: int, joueur_color: chess.Color) -> tuple[int, int]:
    col  = chess.square_file(case)
    rang = chess.square_rank(case)
    if joueur_color == chess.WHITE:
        rang = 7 - rang
    return MARGE + col * TAILLE_CASE, MARGE + rang * TAILLE_CASE


def pixel_vers_case(x: int, y: int, joueur_color: chess.Color) -> int | None:
    bx, by = x - MARGE, y - MARGE
    if not (0 <= bx < TAILLE_PLATEAU and 0 <= by < TAILLE_PLATEAU):
        return None
    col, rang = bx // TAILLE_CASE, by // TAILLE_CASE
    if joueur_color == chess.WHITE:
        rang = 7 - rang
    return chess.square(col, rang)


# ── Rendu plateau ─────────────────────────────────────────────────────────────

def dessiner_plateau(surface: pygame.Surface, board: chess.Board,
                     selection: int | None, joueur_color: chess.Color,
                     dernier_coup: chess.Move | None) -> None:
    # Cadre autour du plateau
    pygame.draw.rect(surface, C_CADRE,
                     (MARGE - 3, MARGE - 3, TAILLE_PLATEAU + 6, TAILLE_PLATEAU + 6))

    overlay = pygame.Surface((TAILLE_CASE, TAILLE_CASE), pygame.SRCALPHA)

    coups_libres:   set[int] = set()
    coups_captures: set[int] = set()
    if selection is not None:
        for m in board.legal_moves:
            if m.from_square == selection:
                (coups_captures if board.is_capture(m) else coups_libres).add(m.to_square)

    roi_en_echec = board.king(board.turn) if board.is_check() else None

    for case in chess.SQUARES:
        col, rang = chess.square_file(case), chess.square_rank(case)
        px, py = case_vers_pixel(case, joueur_color)
        pygame.draw.rect(surface, C_CLAIRE if (col + rang) % 2 == 0 else C_SOMBRE,
                         (px, py, TAILLE_CASE, TAILLE_CASE))

        if dernier_coup and case in (dernier_coup.from_square, dernier_coup.to_square):
            overlay.fill(C_DERNIER)
            surface.blit(overlay, (px, py))

        if case == selection:
            overlay.fill(C_SELECT)
            surface.blit(overlay, (px, py))

        if case == roi_en_echec:
            overlay.fill(C_ECHEC)
            surface.blit(overlay, (px, py))

    # Indicateurs de coups légaux
    dot_surf = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
    for case in coups_libres:
        px, py = case_vers_pixel(case, joueur_color)
        pygame.draw.circle(dot_surf, C_DOT,
                           (px + TAILLE_CASE // 2, py + TAILLE_CASE // 2),
                           TAILLE_CASE // 6)
    for case in coups_captures:
        px, py = case_vers_pixel(case, joueur_color)
        pygame.draw.circle(dot_surf, C_DOT,
                           (px + TAILLE_CASE // 2, py + TAILLE_CASE // 2),
                           TAILLE_CASE // 2 - 2, 7)
    surface.blit(dot_surf, (0, 0))

    # Pièces avec ombre portée
    for case, piece in board.piece_map().items():
        glyphe = GLYPHES[(piece.color, piece.piece_type)]
        px, py = case_vers_pixel(case, joueur_color)
        cx = px + TAILLE_CASE // 2
        cy = py + TAILLE_CASE // 2
        ombre = FONTE_PIECE.render(glyphe, True, (15, 15, 15))
        surface.blit(ombre, (cx - ombre.get_width() // 2 + 2,
                             cy - ombre.get_height() // 2 + 2))
        couleur_p = (255, 255, 255) if piece.color == chess.WHITE else (20, 20, 20)
        texte = FONTE_PIECE.render(glyphe, True, couleur_p)
        surface.blit(texte, (cx - texte.get_width() // 2,
                             cy - texte.get_height() // 2))

    # Coordonnées dans la marge
    for i in range(8):
        lettre = chr(ord('a') + (i if joueur_color == chess.WHITE else 7 - i))
        t = FONTE_COORD.render(lettre, True, C_COORD)
        surface.blit(t, (MARGE + i * TAILLE_CASE + TAILLE_CASE - t.get_width() - 3,
                         MARGE + TAILLE_PLATEAU + 6))
        num = str(8 - i) if joueur_color == chess.WHITE else str(i + 1)
        t = FONTE_COORD.render(num, True, C_COORD)
        surface.blit(t, (5, MARGE + i * TAILLE_CASE + 4))


# ── Rendu panneau ─────────────────────────────────────────────────────────────

def dessiner_panneau(surface: pygame.Surface, board: chess.Board, niveau: int,
                     joueur_color: chess.Color, message: str,
                     prises_blancs: list, prises_noirs: list,
                     temps_affiche: float | None, moteur_en_cours: bool) -> None:
    x0 = MARGE * 2 + TAILLE_PLATEAU
    pygame.draw.rect(surface, C_PANNEAU, (x0, 0, PANNEAU_W, HAUTEUR))
    pygame.draw.line(surface, C_SEP, (x0, 0), (x0, HAUTEUR), 1)

    x = x0 + 14
    y = 18

    def txt(texte: str, fonte=None, couleur=C_TEXTE):
        nonlocal y
        fonte = fonte or FONTE_INFO
        r = fonte.render(texte, True, couleur)
        surface.blit(r, (x, y))
        y += r.get_height() + 5

    def sep():
        nonlocal y
        y += 4
        pygame.draw.line(surface, C_SEP,
                         (x0 + 8, y), (x0 + PANNEAU_W - 8, y), 1)
        y += 10

    ia_color = chess.BLACK if joueur_color == chess.WHITE else chess.WHITE
    ia_nom   = "Noirs" if ia_color == chess.BLACK else "Blancs"

    txt(f"Niveau {niveau} – {NOM_NIVEAU[niveau]}", couleur=C_ACCENT)
    txt(f"IA : {ia_nom}", FONTE_COORD, C_DIM)
    sep()

    tour = "Blancs" if board.turn == chess.WHITE else "Noirs"
    txt(f"Tour : {tour}")
    txt(f"Coup n° {board.fullmove_number}", FONTE_COORD, C_DIM)
    sep()

    if board.is_game_over():
        outcome = board.outcome()
        if outcome and outcome.winner is not None:
            gagnant = "Blancs" if outcome.winner == chess.WHITE else "Noirs"
            txt(f"{gagnant} gagnent !", couleur=C_ACCENT)
        else:
            txt("Match nul", couleur=C_ACCENT)
        txt("R = Rejouer", FONTE_COORD, C_DIM)
    elif moteur_en_cours:
        dots = "." * (int(time.perf_counter() * 2) % 4)
        txt(f"IA réfléchit{dots}", couleur=C_DIM)
        if temps_affiche is not None:
            txt(f"{temps_affiche:.1f}s", FONTE_COORD, C_DIM)
    else:
        txt(message)
        if temps_affiche is not None:
            txt(f"IA : {temps_affiche:.1f}s", FONTE_COORD, C_DIM)
    sep()

    def afficher_prises(prises: list, couleur_piece: chess.Color, label: str):
        nonlocal y
        txt(label, FONTE_COORD, C_DIM)
        if not prises:
            txt("—", FONTE_COORD, C_DIM)
            return
        triees = sorted(prises, key=lambda p: -VALEUR.get(p, 0))
        for i in range(0, len(triees), 6):
            glyph_str = "".join(GLYPHES[(couleur_piece, p)] for p in triees[i:i + 6])
            r = FONTE_CAPS.render(glyph_str, True, C_TEXTE)
            surface.blit(r, (x, y))
            y += r.get_height() + 2
        txt(f"+{sum(VALEUR.get(p, 0) for p in prises)}", FONTE_COORD, C_ACCENT)

    afficher_prises(prises_noirs, chess.BLACK, "Blancs ont pris :")
    afficher_prises(prises_blancs, chess.WHITE, "Noirs ont pris :")
    sep()

    av = (sum(VALEUR.get(p, 0) for p in prises_noirs)
          - sum(VALEUR.get(p, 0) for p in prises_blancs))
    if av > 0:
        txt(f"Avantage Blancs +{av}", FONTE_COORD, C_ACCENT)
    elif av < 0:
        txt(f"Avantage Noirs  +{-av}", FONTE_COORD, C_ACCENT)
    else:
        txt("Matériel égal", FONTE_COORD, C_DIM)


# ── Menu de sélection ─────────────────────────────────────────────────────────

def choisir(ecran: pygame.Surface, titre: str, options: list[str]) -> int:
    clock = pygame.time.Clock()
    while True:
        ecran.fill(C_FOND)
        t = FONTE_INFO.render(titre, True, C_TEXTE)
        ecran.blit(t, (LARGEUR // 2 - t.get_width() // 2, 70))
        pygame.draw.line(ecran, C_SEP, (80, 106), (LARGEUR - 80, 106), 1)

        mx, my = pygame.mouse.get_pos()
        rects = []
        for i, opt in enumerate(options):
            ry = 128 + i * 60
            rect = pygame.Rect(LARGEUR // 2 - 190, ry, 380, 46)
            hovered = rect.collidepoint(mx, my)
            pygame.draw.rect(ecran, (65, 62, 55) if hovered else (42, 40, 36),
                             rect, border_radius=6)
            if hovered:
                pygame.draw.rect(ecran, C_ACCENT, rect, 1, border_radius=6)
            lab = FONTE_INFO.render(f"{i + 1}.  {opt}", True,
                                    C_TEXTE if hovered else C_DIM)
            ecran.blit(lab, (rect.x + 14, rect.y + 13))
            rects.append(rect)

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        return i + 1
            if event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_9:
                choix = event.key - pygame.K_0
                if 1 <= choix <= len(options):
                    return choix
        clock.tick(30)


# ── Boucle principale ─────────────────────────────────────────────────────────

def main() -> None:
    pygame.init()
    ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
    pygame.display.set_caption("ChessBot")
    clock = pygame.time.Clock()

    global FONTE_PIECE, FONTE_INFO, FONTE_COORD, FONTE_CAPS
    for nom in ("Segoe UI Symbol", "DejaVu Sans", "Arial Unicode MS", "FreeSans", None):
        FONTE_PIECE = pygame.font.SysFont(nom, 56)
        FONTE_INFO  = pygame.font.SysFont(nom, 20)
        FONTE_COORD = pygame.font.SysFont(nom, 14)
        FONTE_CAPS  = pygame.font.SysFont(nom, 24)
        if FONTE_PIECE.render("♔", True, (0, 0, 0)).get_width() > 4:
            break

    niveau      = choisir(ecran, "Choisissez un niveau :", [
        "Débutant           (Niveau 0)",
        "Novice               (Niveau 1)",
        "Facile                 (Niveau 2)",
        "Intermédiaire   (Niveau 3)",
        "Fort                   (Niveau 4)",
    ])
    couleur_idx  = choisir(ecran, "Jouez avec quelle couleur ?", ["Blancs", "Noirs"])
    joueur_color = chess.WHITE if couleur_idx == 1 else chess.BLACK

    board = chess.Board()
    selection:    int | None        = None
    dernier_coup: chess.Move | None = None
    message         = "À vous de jouer !"
    moteur_en_cours = False
    prises_blancs: list[chess.PieceType] = []   # pièces blanches prises par les Noirs
    prises_noirs:  list[chess.PieceType] = []   # pièces noires prises par les Blancs
    temps_moteur: float | None = None
    debut_reflexion = 0.0

    _fil:      threading.Thread | None  = None
    _resultat: list[chess.Move | None]  = [None]

    def lancer_moteur() -> None:
        nonlocal moteur_en_cours, debut_reflexion, _fil
        moteur_en_cours = True
        debut_reflexion = time.perf_counter()
        _resultat[0]    = None
        board_copie     = board.copy()
        _fil = threading.Thread(
            target=lambda b=board_copie: _resultat.__setitem__(
                0, engine.best_move(b, niveau)
            ),
            daemon=True,
        )
        _fil.start()

    # Si le joueur choisit les Noirs, l'IA (Blancs) joue en premier
    if joueur_color == chess.BLACK:
        lancer_moteur()

    while True:
        ecran.fill(C_FOND)

        # ── Événements ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                main(); return

            if (event.type == pygame.MOUSEBUTTONDOWN
                    and not board.is_game_over()
                    and board.turn == joueur_color
                    and not moteur_en_cours):

                cc = pixel_vers_case(event.pos[0], event.pos[1], joueur_color)
                if cc is None:
                    selection = None
                elif selection is None:
                    p = board.piece_at(cc)
                    if p and p.color == joueur_color:
                        selection = cc
                else:
                    coup = chess.Move(selection, cc)
                    p_sel = board.piece_at(selection)
                    if (p_sel and p_sel.piece_type == chess.PAWN
                            and chess.square_rank(cc) in (0, 7)):
                        coup = chess.Move(selection, cc, promotion=chess.QUEEN)

                    if coup in board.legal_moves:
                        prise = piece_capturee(board, coup)
                        if prise:
                            (prises_noirs if prise.color == chess.BLACK
                             else prises_blancs).append(prise.piece_type)
                        board.push(coup)
                        dernier_coup = coup
                        selection    = None
                        lancer_moteur()
                    else:
                        p = board.piece_at(cc)
                        selection = cc if (p and p.color == joueur_color) else None

        # ── Réception du résultat du thread moteur ────────────────────────────
        if moteur_en_cours and _fil is not None and not _fil.is_alive():
            temps_moteur = time.perf_counter() - debut_reflexion
            coup_moteur  = _resultat[0]
            if coup_moteur and not board.is_game_over():
                prise = piece_capturee(board, coup_moteur)
                if prise:
                    (prises_noirs if prise.color == chess.BLACK
                     else prises_blancs).append(prise.piece_type)
                board.push(coup_moteur)
                dernier_coup = coup_moteur
            message         = "À vous de jouer !"
            moteur_en_cours = False
            _fil            = None

        temps_affiche = (time.perf_counter() - debut_reflexion
                         if moteur_en_cours else temps_moteur)

        # ── Rendu ─────────────────────────────────────────────────────────────
        dessiner_plateau(ecran, board, selection, joueur_color, dernier_coup)
        dessiner_panneau(ecran, board, niveau, joueur_color, message,
                         prises_blancs, prises_noirs, temps_affiche, moteur_en_cours)
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
