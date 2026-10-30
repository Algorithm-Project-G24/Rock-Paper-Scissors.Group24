"""Rule Engine: pure logic, no camera and no UI."""
ROCK, PAPER, SCISSORS, UNKNOWN = "ROCK", "PAPER", "SCISSORS", "UNKNOWN"
MOVES = (ROCK, PAPER, SCISSORS)
WIN, LOSE, DRAW = "WIN", "LOSE", "DRAW"

BEATS = {ROCK: SCISSORS, PAPER: ROCK, SCISSORS: PAPER}


def decide(player: str, computer: str) -> str:
    """Return WIN / LOSE / DRAW from the player's point of view."""
    if player not in MOVES or computer not in MOVES:
        raise ValueError(f"Invalid move: player={player!r}, computer={computer!r}")
    if player == computer:
        return DRAW
    return WIN if BEATS[player] == computer else LOSE
