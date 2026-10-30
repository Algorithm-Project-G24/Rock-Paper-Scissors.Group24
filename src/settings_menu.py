"""Settings menu logic (no drawing here, so it can be unit-tested).

Keys are strings: 'up' 'down' 'left' 'right' 'enter' 'esc' 'backspace' or a single character.
Row 0 (Name) is typed; every other row is changed with < > (keyboard or the pointing finger).
"""
AVATARS = ("CAT", "PANDA", "FROG", "ROBOT")
LEVELS = ("EASY", "NORMAL", "HARD")
MATCHES = ((3, "First to 3"),)
COUNTDOWNS = (2, 3, 4, 5)
ROWS = ("Name", "Character", "Level", "Match", "Countdown", "Next round", "Sound")
LEVEL_INFO = {
    "EASY": "Computer makes silly mistakes",
    "NORMAL": "Pure luck - a fair fight",
    "HARD": "Computer learns your habits!",
}
MAX_NAME = 10


class SettingsMenu:
    def __init__(self, settings):
        self.s = settings
        self.sel = 0
        self.editing = False

    # ---- what to show --------------------------------------------------
    def value_text(self, i: int) -> str:
        s = self.s
        return [
            s.player_name + ("_" if self.editing else ""),
            s.avatar,
            s.difficulty,
            dict(MATCHES).get(s.target_score, "First to 3"),
            f"{s.countdown_seconds} sec",
            "AUTO" if s.auto_next else "POINT",
            "ON" if s.sound else "OFF",
        ][i]

    # ---- input -----------------------------------------------------------
    def handle(self, key):
        """Returns 'close' when the menu should close, else None."""
        if key is None:
            return None
        if self.editing:
            self._edit_name(key)
            return None
        k = key.lower() if len(key) == 1 else key
        if k in ("up", "w"):
            self.sel = (self.sel - 1) % len(ROWS)
        elif k in ("down", "s"):
            self.sel = (self.sel + 1) % len(ROWS)
        elif k in ("left", "a"):
            self._change(-1)
        elif k in ("right", "d"):
            self._change(+1)
        elif k == "enter":
            if self.sel == 0:
                self.editing = True
            else:
                self._change(+1)
        elif k == "esc":
            if not self.s.player_name.strip():
                self.s.player_name = "PLAYER"
            return "close"
        return None

    def change(self, row: int, delta: int):
        """Used by the pointing-finger < and > buttons."""
        self.sel = row
        self._change(delta)

    def _edit_name(self, key):
        if key in ("enter", "esc"):
            self.editing = False
        elif key == "backspace":
            self.s.player_name = self.s.player_name[:-1]
        elif len(key) == 1 and (key.isalnum() or key in " _-") and len(self.s.player_name) < MAX_NAME:
            self.s.player_name += key

    def _rotate(self, options, current, delta):
        i = options.index(current) if current in options else 0
        return options[(i + delta) % len(options)]

    def _change(self, delta):
        s, r = self.s, self.sel
        if r == 1:
            s.avatar = self._rotate(AVATARS, s.avatar, delta)
        elif r == 2:
            s.difficulty = self._rotate(LEVELS, s.difficulty, delta)
        elif r == 3:
            s.target_score = self._rotate([m[0] for m in MATCHES], s.target_score, delta)
        elif r == 4:
            s.countdown_seconds = self._rotate(COUNTDOWNS, s.countdown_seconds, delta)
        elif r == 5:
            s.auto_next = not s.auto_next
        elif r == 6:
            s.sound = not s.sound
