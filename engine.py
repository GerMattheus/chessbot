import random
import chess
import chess.polyglot
from evaluation import evaluate, PIECE_VALUES

# Profondeur de recherche par niveau (en demi-coups / plies)
DEPTH_BY_LEVEL = {1: 0, 2: 2, 3: 3, 4: 4, 5: 5}

# Table de transposition : zobrist_hash → (profondeur, score, flag)
# flag : 'exact' | 'lower' | 'upper'
_tt: dict[int, tuple[int, int, str]] = {}
_TT_MAX = 500_000   # limite mémoire (~50 Mo environ)


# ── Tri des coups ─────────────────────────────────────────────────────────────

def _score_move(board: chess.Board, move: chess.Move) -> int:
    """
    Heuristique MVV-LVA (Most Valuable Victim – Least Valuable Attacker).
    Les captures de pièces précieuses avec des pièces bon marché passent en premier,
    ce qui maximise les coupures alpha-bêta et permet d'explorer plus profond.
    """
    s = 0
    if board.is_capture(move):
        victime   = board.piece_at(move.to_square)
        attaquant = board.piece_at(move.from_square)
        if victime and attaquant:
            s += 10 * PIECE_VALUES[victime.piece_type] - PIECE_VALUES[attaquant.piece_type]
    if move.promotion:
        s += PIECE_VALUES.get(move.promotion, 0)
    return s


def _order(board: chess.Board, moves: list[chess.Move]) -> list[chess.Move]:
    """Retourne les coups triés du plus prometteur au moins prometteur."""
    return sorted(moves, key=lambda m: _score_move(board, m), reverse=True)


# ── Recherche de quiescence ───────────────────────────────────────────────────

def _quiescence(board: chess.Board, alpha: int, beta: int, level: int) -> int:
    """
    Continue la recherche uniquement sur les captures jusqu'à une position calme.

    Pourquoi ? Sans quiescence, le moteur peut évaluer une position juste avant
    qu'une pièce soit prise (effet d'horizon) et croire à tort qu'elle est bonne.
    En épuisant les captures, on obtient une évaluation fiable.

    Score retourné du point de vue du joueur à qui c'est le tour (convention negamax).
    """
    sign = 1 if board.turn == chess.WHITE else -1
    stand_pat = sign * evaluate(board, level)   # score sans jouer de coup

    if stand_pat >= beta:
        return beta         # coupure bêta : la position est déjà trop bonne pour l'adversaire
    alpha = max(alpha, stand_pat)

    captures = _order(board, [m for m in board.generate_pseudo_legal_captures()
                               if m in board.legal_moves])
    for move in captures:
        board.push(move)
        score = -_quiescence(board, -beta, -alpha, level)
        board.pop()
        if score >= beta:
            return beta
        alpha = max(alpha, score)

    return alpha


# ── Negamax avec alpha-bêta ───────────────────────────────────────────────────

def _negamax(board: chess.Board, depth: int, alpha: int, beta: int,
             level: int, use_tt: bool) -> int:
    """
    Negamax = minimax symétrique : le score est toujours du point de vue
    du joueur actif, ce qui évite d'avoir deux branches max/min séparées.
    Formule clé : score_parent = -negamax(enfant)

    Améliorations par niveau :
      niveau 4 : tri des coups + quiescence à la feuille
      niveau 5 : + table de transposition (cache les positions déjà évaluées)
    """
    alpha_orig = alpha

    # ── Table de transposition (niveau 5) ────────────────────────────────────
    zh = None
    if use_tt:
        zh = chess.polyglot.zobrist_hash(board)
        if zh in _tt:
            tt_depth, tt_score, tt_flag = _tt[zh]
            if tt_depth >= depth:
                if tt_flag == 'exact':
                    return tt_score
                elif tt_flag == 'lower':
                    alpha = max(alpha, tt_score)
                elif tt_flag == 'upper':
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score

    # ── Cas terminaux ────────────────────────────────────────────────────────
    if board.is_game_over():
        if board.is_checkmate():
            # Plus tôt le mat, meilleur c'est ; board.ply() évite les égalités
            return -(900_000 - board.ply())
        return 0    # pat ou nulle

    if depth == 0:
        if level >= 4:
            return _quiescence(board, alpha, beta, level)
        sign = 1 if board.turn == chess.WHITE else -1
        return sign * evaluate(board, level)

    # ── Recherche récursive ───────────────────────────────────────────────────
    moves = _order(board, list(board.legal_moves)) if level >= 4 else list(board.legal_moves)
    best = -10**9

    for move in moves:
        board.push(move)
        score = -_negamax(board, depth - 1, -beta, -alpha, level, use_tt)
        board.pop()
        best = max(best, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break   # coupure bêta

    # ── Stockage en table de transposition ───────────────────────────────────
    if use_tt and zh is not None and len(_tt) < _TT_MAX:
        if best <= alpha_orig:
            flag = 'upper'    # borne supérieure : tous les coups ont été mauvais
        elif best >= beta:
            flag = 'lower'    # borne inférieure : coupure bêta, valeur réelle peut être plus haute
        else:
            flag = 'exact'    # valeur exacte (nœud PV)
        _tt[zh] = (depth, best, flag)

    return best


# ── Point d'entrée public ─────────────────────────────────────────────────────

def best_move(board: chess.Board, level: int) -> chess.Move | None:
    """Retourne le meilleur coup légal pour le camp qui doit jouer, au niveau donné."""
    moves = list(board.legal_moves)
    if not moves:
        return None

    depth = DEPTH_BY_LEVEL.get(level, 2)

    # Niveau 1 : coup purement aléatoire, pas de recherche
    if depth == 0:
        return random.choice(moves)

    use_tt = (level >= 5)
    # Mélange initial pour départager les coups de score identique aléatoirement
    random.shuffle(moves)
    moves = _order(board, moves) if level >= 4 else moves

    best_score = -10**9
    best = moves[0]

    for move in moves:
        board.push(move)
        score = -_negamax(board, depth - 1, -10**9, 10**9, level, use_tt)
        board.pop()
        if score > best_score:
            best_score, best = score, move

    return best
