import random
import chess
from evaluation import evaluate

# Profondeur de recherche par niveau (en demi-coups / plies)
DEPTH_BY_LEVEL = {1: 0, 2: 2, 3: 3}


def _minimax(
    board: chess.Board,
    depth: int,
    alpha: int,
    beta: int,
    maximising: bool,
    level: int,
) -> int:
    """Minimax avec élagage alpha-bêta ; retourne le score du point de vue des Blancs."""
    if depth == 0 or board.is_game_over():
        return evaluate(board, level)

    moves = list(board.legal_moves)

    if maximising:
        best = -10**9
        for move in moves:
            board.push(move)
            best = max(best, _minimax(board, depth - 1, alpha, beta, False, level))
            board.pop()
            alpha = max(alpha, best)
            if alpha >= beta:
                break  # coupure β : la branche ne peut plus améliorer le max
        return best
    else:
        best = 10**9
        for move in moves:
            board.push(move)
            best = min(best, _minimax(board, depth - 1, alpha, beta, True, level))
            board.pop()
            beta = min(beta, best)
            if beta <= alpha:
                break  # coupure α : la branche ne peut plus améliorer le min
        return best


def best_move(board: chess.Board, level: int) -> chess.Move:
    """Retourne le meilleur coup légal pour le camp qui doit jouer, au niveau donné."""
    moves = list(board.legal_moves)
    if not moves:
        return None

    depth = DEPTH_BY_LEVEL.get(level, 2)

    # Niveau 1 : coup purement aléatoire, pas de recherche
    if depth == 0:
        return random.choice(moves)

    maximising = board.turn == chess.WHITE
    best_score = -10**9 if maximising else 10**9
    best = None

    # Mélange pour départager les coups de score identique de façon aléatoire
    random.shuffle(moves)

    for move in moves:
        board.push(move)
        score = _minimax(board, depth - 1, -10**9, 10**9, not maximising, level)
        board.pop()

        if maximising and score > best_score:
            best_score, best = score, move
        elif not maximising and score < best_score:
            best_score, best = score, move

    return best
