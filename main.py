"""Rock Paper Scissors - hand gesture game.   Run:  python main.py

Control it with your hand: point your INDEX FINGER at a button and hold it for about 1 second.
Mouse clicks work too. Keyboard shortcuts:
  S play vs computer | F play vs friend | SPACE start round | T settings | R new game
  C switch camera | M mute | ESC back to menu | Q quit
"""
import time

import cv2
import numpy as np

from src import game_controller as gc
from src.audio import AudioManager
from src.camera import Camera
from src.config import load_settings, save_settings
from src.game_controller import GameController
from src.gesture_classifier import classify, is_pointing
from src.layout import buttons_for
from src.pointer_ui import DwellPointer, hit_test
from src.renderer import Renderer, POINTER_STATES
from src.settings_menu import SettingsMenu

WINDOW = "Rock Paper Scissors"
SPECIAL_KEYS = {2490368: "up", 65362: "up", 2621440: "down", 65364: "down", 2424832: "left", 65361: "left",
                2555904: "right", 65363: "right", 13: "enter", 27: "esc", 8: "backspace", 127: "backspace"}


def read_key():
    """Return 'up'/'down'/'left'/'right'/'enter'/'esc'/'backspace', a single character, or None."""
    k = cv2.waitKeyEx(1)
    if k == -1:
        return None
    if k in SPECIAL_KEYS:
        return SPECIAL_KEYS[k]
    return chr(k) if 0 <= k < 256 else None


def main():
    settings = load_settings()      # remembers name / character / level from last time
    camera = Camera(settings.camera_index, settings.frame_width, settings.frame_height, settings.mirror)
    if not camera.open():
        print("ERROR: no webcam found. Plug one in or change camera_index in src/config.py")
        return 1

    try:
        from src.hand_tracker import HandTracker, primary_hand, should_split_players, split_players
        tracker = HandTracker(settings)
    except ImportError as e:
        print(f"ERROR: mediapipe failed to load: {e}")
        camera.release()
        return 1

    audio = AudioManager(settings.sound)
    ctrl = GameController(settings)
    menu = SettingsMenu(settings)
    renderer = Renderer()
    pointer = DwellPointer()
    blank = np.zeros((settings.frame_height, settings.frame_width, 3), np.uint8)
    last_retry, fps, t_prev = 0.0, 0.0, time.time()
    prev_state, prev_count = ctrl.state, None
    clicks = []

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback(WINDOW, lambda e, x, y, f, p: clicks.append((x, y)) if e == cv2.EVENT_LBUTTONDOWN else None)

    def do_action(action):
        """One handler for finger, mouse and (some) keyboard actions."""
        audio.play("tick")
        if action == "PLAY_CPU":
            ctrl.start_game(gc.CPU)
        elif action == "PLAY_FRIEND":
            ctrl.start_game(gc.FRIEND)
        elif action == "SETTINGS":
            menu.editing = False
            ctrl.open_settings()
        elif action == "QUIT":
            ctrl.exit()
        elif action in ("START_ROUND", "NEXT_ROUND"):
            ctrl.start_round()
        elif action == "NEW_GAME":
            ctrl.new_game()
        elif action == "MENU":
            ctrl.go_home()
        elif action == "BACK":
            save_settings(settings)
            ctrl.close_settings()
        elif action == "EDIT_NAME":
            menu.sel, menu.editing = 0, True
        elif action.startswith("ROW:"):
            _, row, delta = action.split(":")
            menu.change(int(row), int(delta))

    while ctrl.state != gc.EXIT:
        frame = camera.read()
        camera_ok = frame is not None
        g1, hp1, g2, hp2, pointer_pos = "UNKNOWN", False, "UNKNOWN", False, None

        if camera_ok:
            fh, fw = frame.shape[:2]
            hands = tracker.detect(frame)
            if should_split_players(ctrl.mode, ctrl.state):
                a, b = split_players(hands)          # P1 = left half, P2 = right half
                if a:
                    g1, hp1 = classify(a[0], settings.finger_extend_ratio), True
                if b:
                    g2, hp2 = classify(b[0], settings.finger_extend_ratio), True
            else:
                a = primary_hand(hands)
                if a:
                    g1, hp1 = classify(a[0], settings.finger_extend_ratio), True
                    if is_pointing(a[0], settings.finger_extend_ratio):
                        pointer_pos = (int(a[0][8][0] * fw), int(a[0][8][1] * fh))   # index fingertip
            for _, lm_obj in hands:
                tracker.draw(frame, lm_obj)
        else:   # camera disconnected: keep running and try to reconnect every second
            frame = blank.copy()
            if time.time() - last_retry > 1.0:
                last_retry = time.time()
                camera.open()

        ctrl.update(g1, hp1, g2, hp2)
        audio.enabled = settings.sound

        # ---- finger pointer + mouse -> actions ----
        if ctrl.state in POINTER_STATES:
            buttons = buttons_for(ctrl, frame.shape[1], frame.shape[0])
            action = pointer.update(pointer_pos, buttons)
            if action:
                do_action(action)
            for cx, cy in clicks:
                b = hit_test(buttons_for(ctrl, frame.shape[1], frame.shape[0]), (cx, cy))
                if b:
                    do_action(b.id)
        else:
            pointer.reset()
            pointer_pos = None
        clicks.clear()

        # ---- sounds ----
        if ctrl.state != prev_state:
            if ctrl.state == gc.COUNTDOWN:
                audio.play("start")
            elif ctrl.state == gc.CAPTURE:
                audio.play("go")
            elif ctrl.state == gc.GAME_OVER:
                audio.play("win" if (ctrl.winner == "PLAYER" or ctrl.mode == gc.FRIEND) else "lose")
            prev_state, prev_count = ctrl.state, None
        if ctrl.state == gc.COUNTDOWN and ctrl.countdown_value != prev_count:
            prev_count = ctrl.countdown_value
            audio.play("tick")
        for kind, result in renderer.events:
            if kind == "reveal":
                audio.play("win" if (ctrl.mode == gc.FRIEND and result != "DRAW") else result.lower())
        renderer.events.clear()

        now = time.time()
        fps = 0.9 * fps + 0.1 / max(now - t_prev, 1e-6)
        t_prev = now
        in_pointer_state = ctrl.state in POINTER_STATES
        cv2.imshow(WINDOW, renderer.render(frame, ctrl, g1, fps, camera_ok, not settings.sound, menu,
                                           pointer if in_pointer_state else None, pointer_pos))

        key = read_key()
        if ctrl.state == gc.SETTINGS:           # the menu owns the keyboard (so typing a name can't quit)
            if menu.handle(key) == "close":
                do_action("BACK")
            continue
        k = key.lower() if key and len(key) == 1 else key
        if k == "q":
            ctrl.exit()
        elif k == "esc":                         # ESC = go back to the menu (quit if already there)
            ctrl.exit() if ctrl.state == gc.HOME else ctrl.go_home()
        elif k == "s":
            ctrl.start_game(gc.CPU)
        elif k == "f":
            ctrl.start_game(gc.FRIEND)
        elif k == " ":
            ctrl.start_round()
        elif k == "r":
            ctrl.new_game()
        elif k == "t":
            do_action("SETTINGS")
        elif k == "c":
            camera.switch()
        elif k == "m":
            settings.sound = not settings.sound
            save_settings(settings)

    # FR-12: release everything safely
    tracker.close()
    camera.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
