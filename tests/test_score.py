import pytest
from src.score_manager import ScoreManager
from src.history import RoundHistory


def test_counts_and_reset():
    s = ScoreManager()
    for r in ["WIN", "WIN", "LOSE", "DRAW"]:
        s.record(r)
    assert (s.player, s.computer, s.draws, s.rounds) == (2, 1, 1, 4)
    s.reset()
    assert s.rounds == 0


def test_target_score():
    s = ScoreManager()
    s.record("WIN"); s.record("WIN")
    assert s.winner(3) is None and s.winner(0) is None
    s.record("WIN")
    assert s.winner(3) == "PLAYER"


def test_invalid_result():
    with pytest.raises(ValueError):
        ScoreManager().record("MAYBE")


def test_history_keeps_recent_only():
    h = RoundHistory(size=3)
    for i in range(5):
        h.add("ROCK", "PAPER", "LOSE")
    assert len(h) == 3
    h.clear()
    assert len(h) == 0
