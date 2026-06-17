import random
import chess
from evaluation import evaluate

# Search depth by level (in half-moves / plies)
DEPTH_BY_LEVEL = {1: 0, 2: 2, 3: 3}


def _minimax(
    board: chess.Board,
    depth: int,
    alpha: int,
    beta: int,
    maximising: bool,
    level: int,
) -> int:
    """Alpha-beta pruned minimax; returns score from White's perspective."""
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
                break  # β cut-off
        return best
    else:
        best = 10**9
        for move in moves:
            board.push(move)
            best = min(best, _minimax(board, depth - 1, alpha, beta, True, level))
            board.pop()
            beta = min(beta, best)
            if beta <= alpha:
                break  # α cut-off
        return best


def best_move(board: chess.Board, level: int) -> chess.Move:
    """Return the best legal move for the side to move at the given level."""
    moves = list(board.legal_moves)
    if not moves:
        return None

    depth = DEPTH_BY_LEVEL.get(level, 2)

    # Level 1: pure random
    if depth == 0:
        return random.choice(moves)

    maximising = board.turn == chess.WHITE
    best_score = -10**9 if maximising else 10**9
    best = None

    # Shuffle to break ties randomly
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
