import random
import time
import chess
import chess.polyglot
from evaluation import evaluate, PIECE_VALUES

# Profondeur maximale cible par niveau (en demi-coups / plies)
DEPTH_BY_LEVEL = {1: 0, 2: 2, 3: 3, 4: 4, 5: 5}

# Budget temps par coup (secondes) pour les niveaux avec deepening itératif
_TIME_BUDGET = {4: 1.0, 5: 2.5}

# Table de transposition : zobrist_hash → (profondeur, score, flag)
_tt: dict[int, tuple[int, int, str]] = {}
_TT_MAX = 500_000

# État global de la recherche (réinitialisé à chaque appel best_move)
_time_up  = [False]
_deadline = [0.0]
_nodes    = [0]


# ── Tri des coups (MVV-LVA) ───────────────────────────────────────────────────

def _score_move(board: chess.Board, move: chess.Move) -> int:
    """Heuristique MVV-LVA : capturer une pièce chère avec une pièce bon marché en premier."""
    s = 0
    if board.is_capture(move):
        victim   = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if victim and attacker:
            s += 10 * PIECE_VALUES[victim.piece_type] - PIECE_VALUES[attacker.piece_type]
    if move.promotion:
        s += PIECE_VALUES.get(move.promotion, 0)
    return s


def _order(board: chess.Board, moves: list[chess.Move]) -> list[chess.Move]:
    return sorted(moves, key=lambda m: _score_move(board, m), reverse=True)


# ── Quiescence search ─────────────────────────────────────────────────────────

def _quiescence(board: chess.Board, alpha: int, beta: int, level: int, qdepth: int = 2) -> int:
    """
    Continue uniquement sur les captures pour éviter l'effet d'horizon.
    qdepth limite la profondeur extra pour maîtriser le temps de calcul.
    Score du point de vue du joueur actif (convention negamax).
    """
    if _time_up[0]:
        return 0

    sign = 1 if board.turn == chess.WHITE else -1
    stand_pat = sign * evaluate(board, level)

    if stand_pat >= beta:
        return beta
    if qdepth == 0:
        return max(alpha, stand_pat)
    alpha = max(alpha, stand_pat)

    captures = _order(board, [m for m in board.generate_pseudo_legal_captures()
                               if m in board.legal_moves])
    for move in captures:
        board.push(move)
        score = -_quiescence(board, -beta, -alpha, level, qdepth - 1)
        board.pop()
        if score >= beta:
            return beta
        alpha = max(alpha, score)

    return alpha


# ── Negamax avec alpha-bêta ───────────────────────────────────────────────────

def _negamax(board: chess.Board, depth: int, alpha: int, beta: int,
             level: int, use_tt: bool) -> int:
    """
    Negamax : score toujours du point de vue du joueur actif.
    Formule clé : score_parent = -negamax(enfant, -β, -α).

    Vérification du temps toutes les 2048 nœuds (via masque bit),
    pour limiter l'overhead de time.perf_counter().
    """
    _nodes[0] += 1
    if not (_nodes[0] & 0x7FF):           # tous les 2048 nœuds
        if time.perf_counter() >= _deadline[0]:
            _time_up[0] = True
    if _time_up[0]:
        return 0                           # valeur invalide, ignorée par l'appelant

    alpha_orig = alpha

    # ── Table de transposition ────────────────────────────────────────────────
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
        return -(900_000 - board.ply()) if board.is_checkmate() else 0

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

        if _time_up[0]:
            return 0

        best  = max(best, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break   # coupure bêta

    # ── Stockage en table de transposition ───────────────────────────────────
    if use_tt and zh is not None and len(_tt) < _TT_MAX and not _time_up[0]:
        flag = ('upper' if best <= alpha_orig else
                'lower' if best >= beta       else 'exact')
        _tt[zh] = (depth, best, flag)

    return best


# ── Recherche à une profondeur fixée ─────────────────────────────────────────

def _search_root(board: chess.Board, depth: int,
                 level: int, use_tt: bool) -> chess.Move | None:
    """
    Parcourt tous les coups racine à la profondeur donnée.
    Retourne None si le budget temps est dépassé en cours de route.
    """
    moves = _order(board, list(board.legal_moves))
    best_score = -10**9
    best       = None

    for move in moves:
        if _time_up[0]:
            return None
        board.push(move)
        score = -_negamax(board, depth - 1, -10**9, 10**9, level, use_tt)
        board.pop()
        if not _time_up[0] and score > best_score:
            best_score, best = score, move

    return best if not _time_up[0] else None


# ── Point d'entrée public ─────────────────────────────────────────────────────

def best_move(board: chess.Board, level: int) -> chess.Move | None:
    """
    Retourne le meilleur coup légal pour le camp qui doit jouer.

    Niveaux 1-3 : recherche directe à profondeur fixe (toujours < 1 s).
    Niveaux 4-5 : deepening itératif — on cherche profondeur 1, 2, 3…
                  jusqu'à épuisement du budget temps, et on retient le
                  résultat de la dernière profondeur complète.
    """
    moves = list(board.legal_moves)
    if not moves:
        return None

    depth = DEPTH_BY_LEVEL.get(level, 2)
    if depth == 0:
        return random.choice(moves)

    use_tt = (level >= 5)
    random.shuffle(moves)   # équilibre les égalités de score

    budget = _TIME_BUDGET.get(level, float('inf'))
    _deadline[0] = time.perf_counter() + budget
    _time_up[0]  = False
    _nodes[0]    = 0

    if level <= 3:
        # Profondeur fixe, assez rapide pour ne pas nécessiter de limite
        result = _search_root(board, depth, level, use_tt)
        return result or random.choice(moves)

    # Niveaux 4-5 : deepening itératif
    best = moves[0]                        # coup de secours si tout échoue
    for d in range(1, depth + 1):
        if _time_up[0]:
            break
        result = _search_root(board, d, level, use_tt)
        if result is not None:             # profondeur d complète : valide
            best = result
        if _time_up[0]:
            break

    return best
