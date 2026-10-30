"""Computer Player with three levels. It only ever uses the player's PAST moves,
never the current one, so it cannot cheat.

EASY   - makes silly mistakes: 40% of the time it plays what loses to your predicted move.
NORMAL - pure random, a fair 1/3 chance each.
HARD   - learns your habits: 65% of the time it plays the counter to your predicted move,
         otherwise random, so it is never fully predictable.
"""
import random
from collections import Counter

from .game_rules import MOVES, BEATS

LEVELS = ("EASY", "NORMAL", "HARD")


def predict_next(history):
    """Guess the player's next move from past moves (order-1 pattern, else most frequent)."""
    if len(history) < 3:
        return None
    last = history[-1]
    followers = [history[i + 1] for i in range(len(history) - 1) if history[i] == last]
    pool = followers if len(followers) >= 2 else history
    return Counter(pool).most_common(1)[0][0]


def counter_to(move):
    """The move that beats `move`."""
    return next(k for k, v in BEATS.items() if v == move)


class ComputerPlayer:
    def __init__(self, rng=None):
        self._rng = rng or random.Random()

    def choose(self, player_history=None, level="NORMAL") -> str:
        pred = predict_next(list(player_history or []))
        if pred is not None:
            if level == "HARD" and self._rng.random() < 0.65:
                return counter_to(pred)
            if level == "EASY" and self._rng.random() < 0.40:
                return BEATS[pred]          # deliberately loses to the predicted move
        return self._rng.choice(MOVES)
