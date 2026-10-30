"""Gesture Stabilizer: removes frame-to-frame noise."""
from collections import Counter, deque


class GestureStabilizer:
    def __init__(self, window=10, ratio=0.7, min_frames=6):
        self.window, self.ratio, self.min_frames = window, ratio, min_frames
        self._buf = deque(maxlen=window)

    def reset(self):
        self._buf.clear()

    def push(self, gesture: str):
        self._buf.append(gesture)

    def current(self):
        """Most common valid gesture so far, or None."""
        valid = [g for g in self._buf if g != "UNKNOWN"]
        return Counter(valid).most_common(1)[0][0] if valid else None

    def locked(self):
        """Return the stable gesture once enough frames agree, else None."""
        if len(self._buf) < self.min_frames:
            return None
        g = self.current()
        if g is None:
            return None
        share = sum(1 for x in self._buf if x == g) / len(self._buf)
        return g if share >= self.ratio else None

    def progress(self) -> float:
        """0.0 - 1.0: how close we are to locking a move (for the progress bar)."""
        g = self.current()
        if g is None or not self._buf:
            return 0.0
        share = sum(1 for x in self._buf if x == g) / len(self._buf)
        filled = min(len(self._buf) / self.min_frames, 1.0)
        return max(0.0, min(1.0, filled * share / self.ratio))
