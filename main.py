import chess
import engine

LEVELS = {
    1: "Débutant    – coups aléatoires",
    2: "Novice      – matériel, prof. 2",
    3: "Facile      – matériel + positions, prof. 3",
    4: "Intermédiaire – structure + quiescence, prof. 4",
    5: "Fort        – tout + transpositions, prof. 5",
}


def _print_board(board: chess.Board, player_color: chess.Color) -> None:
    """Affiche le plateau orienté vers le joueur humain."""
    flipped = player_color == chess.BLACK
    print()
    print(board.__str__() if not flipped else chess.Board(board.fen()).transform(chess.flip_vertical).__str__())
    print()


def _get_player_move(board: chess.Board) -> chess.Move | None:
    """Demande un coup à l'humain en notation UCI jusqu'à ce qu'un coup légal soit saisi."""
    while True:
        raw = input("Votre coup (ex: e2e4, ou 'quit') : ").strip().lower()
        if raw == "quit":
            return None
        try:
            move = chess.Move.from_uci(raw)
            if move in board.legal_moves:
                return move
            print("  Coup illégal, réessayez.")
        except ValueError:
            print("  Format invalide. Utilisez la notation UCI (ex: e2e4, g1f3).")


def _choose(prompt: str, options: dict) -> int:
    """Affiche un menu numéroté et retourne la clé choisie."""
    print(prompt)
    for k, v in options.items():
        print(f"  {k}. {v}")
    while True:
        try:
            choice = int(input("> "))
            if choice in options:
                return choice
        except ValueError:
            pass
        print(f"  Entrez un chiffre parmi {list(options.keys())}.")


def main() -> None:
    print("=== Moteur d'échecs Python ===\n")

    level = _choose("Choisissez un niveau :", LEVELS)

    color_choice = _choose(
        "Jouez avec quelle couleur ?",
        {1: "Blancs", 2: "Noirs"},
    )
    player_color = chess.WHITE if color_choice == 1 else chess.BLACK

    board = chess.Board()
    print(f"\nNiveau : {LEVELS[level]}  |  Vous jouez les {'Blancs' if player_color == chess.WHITE else 'Noirs'}")
    print("Entrez vos coups en notation UCI (ex: e2e4). Tapez 'quit' pour quitter.\n")

    while not board.is_game_over():
        _print_board(board, player_color)

        if board.turn == player_color:
            move = _get_player_move(board)
            if move is None:
                print("Partie abandonnée.")
                return
        else:
            print("Le moteur réfléchit…")
            move = engine.best_move(board, level)
            if move is None:
                break
            print(f"  Coup du moteur : {move.uci()}")

        board.push(move)

    _print_board(board, player_color)
    result = board.result()
    outcome = board.outcome()
    if outcome and outcome.winner is not None:
        winner = "Blancs" if outcome.winner == chess.WHITE else "Noirs"
        print(f"Partie terminée — {winner} gagnent ! ({result})")
    else:
        print(f"Partie terminée — Match nul ({result})")


if __name__ == "__main__":
    main()
