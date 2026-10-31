"""Hand Tracker (MediaPipe Hands).

detect() returns every visible hand as (landmarks, mediapipe_object), where landmarks is a list of
21 normalised (x, y, z) points. primary_hand() / split_players() are plain functions (easy to test).
"""
import cv2


def _area(hand) -> float:
    xs, ys = [p[0] for p in hand[0]], [p[1] for p in hand[0]]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def primary_hand(hands):
    """One-player mode: the biggest hand (= closest to the camera). None if no hand."""
    return max(hands, key=_area) if hands else None


def split_players(hands):
    """Two-player mode: (player 1, player 2) = best hand in the left / right half of the picture.
    The picture is mirrored, so each player simply uses the half in front of them."""
    left = [h for h in hands if h[0][0][0] < 0.5]       # wrist x < half
    right = [h for h in hands if h[0][0][0] >= 0.5]
    return (max(left, key=_area) if left else None,
            max(right, key=_area) if right else None)


def should_split_players(mode, state):
    return mode == "FRIEND" and state in ("COUNTDOWN", "CAPTURE")


class HandTracker:
    def __init__(self, settings):
        import mediapipe as mp   # imported here so the rest of the project is testable without it
        self.s = settings
        self._mp = mp
        self._hands = mp.solutions.hands.Hands(
            max_num_hands=max(2, settings.max_hands),
            min_detection_confidence=settings.detection_confidence,
            min_tracking_confidence=settings.tracking_confidence)
        self._draw = mp.solutions.drawing_utils

    def detect(self, frame_bgr):
        res = self._hands.process(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        if not res.multi_hand_landmarks:
            return []
        return [([(p.x, p.y, p.z) for p in lm.landmark], lm) for lm in res.multi_hand_landmarks]

    def draw(self, frame, landmark_obj):
        if landmark_obj is not None:
            self._draw.draw_landmarks(frame, landmark_obj, self._mp.solutions.hands.HAND_CONNECTIONS)

    def close(self):
        self._hands.close()
