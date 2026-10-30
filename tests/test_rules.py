import pytest
from src.game_rules import decide, MOVES


@pytest.mark.parametrize("p,c", [("ROCK", "SCISSORS"), ("PAPER", "ROCK"), ("SCISSORS", "PAPER")])
def test_win(p, c):
    assert decide(p, c) == "WIN"


@pytest.mark.parametrize("p,c", [("ROCK", "PAPER"), ("PAPER", "SCISSORS"), ("SCISSORS", "ROCK")])
def test_lose(p, c):
    assert decide(p, c) == "LOSE"


@pytest.mark.parametrize("m", MOVES)
def test_draw(m):
    assert decide(m, m) == "DRAW"


@pytest.mark.parametrize("bad", ["UNKNOWN", "", None, "LIZARD"])
def test_invalid_move_gives_no_result(bad):
    with pytest.raises(ValueError):
        decide(bad, "ROCK")
