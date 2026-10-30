"""Gesture Classifier.

Input : 21 hand landmarks as (x, y) or (x, y, z) tuples (MediaPipe order).
Output: only 'ROCK', 'PAPER', 'SCISSORS' or 'UNKNOWN'. It knows nothing about the game.

Method: a finger is "extended" when its tip is clearly farther from the wrist than
its PIP joint. This works for any hand rotation and for left or right hands.
The thumb is ignored on purpose (it is the least reliable finger).
"""
import math

WRIST = 0
# (tip, pip) landmark indices for index, middle, ring, pinky
FINGERS = {"index": (8, 6), "middle": (12, 10), "ring": (16, 14), "pinky": (20, 18)}


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def finger_states(landmarks, ratio: float = 1.10) -> dict:
    wrist = landmarks[WRIST]
    return {
        name: _dist(landmarks[tip], wrist) > ratio * _dist(landmarks[pip], wrist)
        for name, (tip, pip) in FINGERS.items()
    }


def classify(landmarks, ratio: float = 1.10) -> str:
    if landmarks is None or len(landmarks) < 21:
        return "UNKNOWN"
    s = finger_states(landmarks, ratio)
    up = sum(s.values())
    if up == 0:
        return "ROCK"
    if up == 4:
        return "PAPER"
    if s["index"] and s["middle"] and not s["ring"] and not s["pinky"]:
        return "SCISSORS"
    return "UNKNOWN"


def is_pointing(landmarks, ratio: float = 1.10) -> bool:
    """True when only the index finger is up (used as a 'mouse pointer' in the menus).
    Kept separate from classify() so the game gestures stay ROCK/PAPER/SCISSORS/UNKNOWN only."""
    if landmarks is None or len(landmarks) < 21:
        return False
    s = finger_states(landmarks, ratio)
    return s["index"] and not (s["middle"] or s["ring"] or s["pinky"])
