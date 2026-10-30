"""Central settings (Settings Manager). Change values here, or in the in-game Settings screen (press T)."""
import json
import os
from dataclasses import dataclass


@dataclass
class Settings:
    # Player (editable in the Settings screen)
    player_name: str = "PLAYER"
    avatar: str = "CAT"             # CAT | PANDA | FROG | ROBOT
    difficulty: str = "NORMAL"      # EASY | NORMAL | HARD

    # Camera
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    mirror: bool = True              # flip image like a mirror

    # Hand tracking
    max_hands: int = 2
    detection_confidence: float = 0.6
    tracking_confidence: float = 0.5
    primary_hand_policy: str = "largest"   # "largest" | "right" | "left"

    # Gesture classification
    finger_extend_ratio: float = 1.10  # tip-to-wrist distance / pip-to-wrist distance

    # Stabilizer
    stability_window: int = 10         # number of recent frames
    stability_ratio: float = 0.7       # share of frames that must agree
    stability_min_frames: int = 6

    # Game flow
    countdown_seconds: int = 3
    capture_timeout: float = 4.0       # seconds to show a valid gesture after GO
    result_seconds: float = 2.5
    auto_next: bool = False            # False = point at NEXT ROUND (or press SPACE); True = starts by itself
    auto_next_seconds: float = 2.0
    target_score: int = 3              # First to 3 wins the match
    history_size: int = 8

    # Optional
    sound: bool = True               # simple beeps (Windows only, no files needed)


SETTINGS_FILE = os.path.join("data", "settings.json")
SAVED_FIELDS = ("player_name", "avatar", "difficulty", "target_score", "countdown_seconds", "auto_next", "sound")


def load_settings(path: str = SETTINGS_FILE) -> Settings:
    """Defaults, overridden by whatever was saved last time (bad/missing file is ignored)."""
    s = Settings()
    try:
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        for k in SAVED_FIELDS:
            if k in saved and type(saved[k]) is type(getattr(s, k)):
                setattr(s, k, saved[k])
        s.target_score = 3
    except (OSError, ValueError):
        pass
    return s


def save_settings(s: Settings, path: str = SETTINGS_FILE):
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({k: getattr(s, k) for k in SAVED_FIELDS}, f, indent=2)
    except OSError:
        pass   # saving is a convenience; never crash the game for it
