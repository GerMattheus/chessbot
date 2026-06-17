import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

# Tables de positions (du point de vue des Blancs, a1=index 0)
# fmt: off
_PST_PAWN = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]
_PST_KNIGHT = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]
_PST_BISHOP = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]
_PST_ROOK = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]
_PST_QUEEN = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]
_PST_KING = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]
# fmt: on

_PST = {
    chess.PAWN:   _PST_PAWN,
    chess.KNIGHT: _PST_KNIGHT,
    chess.BISHOP: _PST_BISHOP,
    chess.ROOK:   _PST_ROOK,
    chess.QUEEN:  _PST_QUEEN,
    chess.KING:   _PST_KING,
}


def _pst_score(piece_type: int, square: int, color: chess.Color) -> int:
    """Retourne le bonus positionnel d'une pièce sur une case donnée (POV Blancs)."""
    # Miroir vertical pour les Noirs : l'index 0 reste sur la rangée 1 pour les deux couleurs
    idx = square if color == chess.WHITE else chess.square_mirror(square)
    return _PST[piece_type][idx]


def _pawn_structure(board: chess.Board) -> int:
    """
    Pénalités de structure de pions (niveau 4+), du point de vue des Blancs.

    - Pions doublés : -20 par pion supplémentaire sur la même colonne.
    - Pions isolés  : -15 par pion sans voisin sur les colonnes adjacentes.
    """
    score = 0
    for color, sign in ((chess.WHITE, 1), (chess.BLACK, -1)):
        pawns = list(board.pieces(chess.PAWN, color))
        files  = [chess.square_file(sq) for sq in pawns]

        for f in range(8):
            count = files.count(f)
            if count > 1:
                score -= sign * 20 * (count - 1)   # pions doublés

        for sq in pawns:
            f = chess.square_file(sq)
            voisin = any(chess.square_file(p) in (f - 1, f + 1) for p in pawns if p != sq)
            if not voisin:
                score -= sign * 15                  # pion isolé

    return score


def evaluate(board: chess.Board, level: int) -> int:
    """
    Évaluation statique de *board* en centipions, du point de vue des Blancs.

    niveau 1 → toujours 0              (coups aléatoires)
    niveau 2 → matériel brut
    niveau 3 → matériel + PST
    niveau 4 → matériel + PST + structure de pions
    niveau 5 → identique au niveau 4 (la force vient de l'algorithme)
    """
    if level == 1:
        return 0

    score = 0
    for square, piece in board.piece_map().items():
        value = PIECE_VALUES[piece.piece_type]
        if level >= 3:
            value += _pst_score(piece.piece_type, square, piece.color)
        score += value if piece.color == chess.WHITE else -value

    if level >= 4:
        score += _pawn_structure(board)

    return score
