"""Audio Manager: tiny beep melodies using Windows' built-in winsound (no extra files/packages).
On other systems it silently does nothing. Press M in the game to mute / unmute."""
import threading

try:
    import winsound
except ImportError:          # Mac / Linux
    winsound = None

PATTERNS = {
    "start": [(659, 90), (784, 90)],
    "tick":  [(880, 70)],
    "go":    [(1320, 220)],
    "win":   [(523, 110), (659, 110), (784, 110), (1047, 320)],
    "lose":  [(392, 180), (330, 180), (262, 420)],
    "draw":  [(440, 140), (440, 140)],
}


class AudioManager:
    def __init__(self, enabled=True):
        self.available = winsound is not None
        self.enabled = enabled

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled

    def play(self, name: str):
        if not (self.enabled and self.available) or name not in PATTERNS:
            return
        threading.Thread(target=self._run, args=(PATTERNS[name],), daemon=True).start()

    @staticmethod
    def _run(notes):
        for freq, ms in notes:
            try:
                winsound.Beep(freq, ms)
            except RuntimeError:
                return
