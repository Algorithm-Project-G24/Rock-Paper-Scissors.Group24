"""Score Manager."""
from .game_rules import WIN, LOSE, DRAW


class ScoreManager:
    def __init__(self):
        self.reset()

    def reset(self):
        self.player = 0
        self.computer = 0
        self.draws = 0

    @property
    def rounds(self) -> int:
        return self.player + self.computer + self.draws

    def record(self, result: str):
        if result == WIN:
            self.player += 1
        elif result == LOSE:
            self.computer += 1
        elif result == DRAW:
            self.draws += 1
        else:
            raise ValueError(f"Invalid result: {result!r}")

    def winner(self, target: int):
        """Return 'PLAYER' / 'COMPUTER' when target reached, else None. target<=0 = free play."""
        if target <= 0:
            return None
        if self.player >= target:
            return "PLAYER"
        if self.computer >= target:
            return "COMPUTER"
        return None
