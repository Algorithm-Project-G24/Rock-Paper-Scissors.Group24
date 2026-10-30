"""Finger-pointer UI: point your index finger at a button and HOLD to 'click' (like a mouse hover-click).

Pure logic (no drawing, no camera) so it is easy to test.
"""
import time
from dataclasses import dataclass


@dataclass
class Button:
    id: str
    label: str
    x: int
    y: int
    w: int
    h: int
    color: tuple = (200, 120, 60)    # BGR

    def contains(self, px, py) -> bool:
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h


def hit_test(buttons, pos):
    if pos is None:
        return None
    return next((b for b in buttons if b.contains(*pos)), None)


class DwellPointer:
    """Hold the pointer on a button for `dwell` seconds to activate it."""

    def __init__(self, dwell=0.9, cooldown=0.8, grace=0.25, clock=time.monotonic):
        self.dwell, self.cooldown, self.grace, self.clock = dwell, cooldown, grace, clock
        self.reset()

    def reset(self):
        self.hover = None          # id of the button being hovered
        self.progress = 0.0        # 0..1
        self._t0 = 0.0
        self._seen = 0.0
        self._cool_until = 0.0

    def update(self, pos, buttons):
        """Call every frame. `pos` = (x, y) fingertip or None. Returns a button id when activated."""
        now = self.clock()
        if now < self._cool_until:
            self.hover, self.progress = None, 0.0
            return None
        if pos is None:
            if now - self._seen > self.grace:       # short tracking dropouts are forgiven
                self.hover, self.progress = None, 0.0
            return None
        self._seen = now
        b = hit_test(buttons, pos)
        if b is None:
            self.hover, self.progress = None, 0.0
            return None
        if b.id != self.hover:
            self.hover, self._t0 = b.id, now
        self.progress = min((now - self._t0) / self.dwell, 1.0)
        if self.progress >= 1.0:
            self._cool_until = now + self.cooldown
            self.hover, self.progress = None, 0.0
            return b.id
        return None
