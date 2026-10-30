"""Build synthetic hand landmarks (wrist at origin, fingers pointing up) for tests."""
import math

BASE = {"index": (5, 6, 7, 8), "middle": (9, 10, 11, 12), "ring": (13, 14, 15, 16), "pinky": (17, 18, 19, 20)}
X = {"index": -0.3, "middle": -0.1, "ring": 0.1, "pinky": 0.3}


def make_hand(extended, rotate_deg=0.0):
    pts = [(0.0, 0.0, 0.0)] * 21
    pts = list(pts)
    pts[1:5] = [(-0.4, 0.3, 0), (-0.5, 0.5, 0), (-0.55, 0.65, 0), (-0.6, 0.8, 0)]  # thumb
    for name, (mcp, pip, dip, tip) in BASE.items():
        x = X[name]
        pts[mcp] = (x, 0.5, 0)
        pts[pip] = (x, 0.8, 0)
        if extended[name]:
            pts[dip], pts[tip] = (x, 1.0, 0), (x, 1.2, 0)
        else:  # curled back toward the palm
            pts[dip], pts[tip] = (x, 0.65, 0), (x, 0.45, 0)
    a = math.radians(rotate_deg)
    return [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a), z) for x, y, z in pts]


ROCK = dict(index=False, middle=False, ring=False, pinky=False)
PAPER = dict(index=True, middle=True, ring=True, pinky=True)
SCISSORS = dict(index=True, middle=True, ring=False, pinky=False)
