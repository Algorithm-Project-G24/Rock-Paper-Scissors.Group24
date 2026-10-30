"""Which buttons exist on which screen, and where. Used by the renderer (to draw them) and main.py (to hit-test)."""
from . import game_controller as gc
from .pointer_ui import Button
from .settings_menu import ROWS

GREEN, BLUE, PURPLE, RED, GREY, YELLOW = (70, 170, 70), (200, 130, 40), (170, 70, 130), (60, 60, 200), (110, 100, 100), (30, 170, 200)
SET_Y0, SET_DY = 92, 42            # settings rows


def row_y(i: int) -> int:
    return SET_Y0 + i * SET_DY


def buttons_for(ctrl, w=640, h=480):
    st = ctrl.state
    cx = w // 2
    if st == gc.HOME:
        return [Button("PLAY_CPU", "PLAY vs COMPUTER", cx - 150, 168, 300, 50, GREEN),
                Button("PLAY_FRIEND", "PLAY vs FRIEND", cx - 150, 228, 300, 50, BLUE),
                Button("SETTINGS", "SETTINGS", cx - 150, 288, 300, 50, PURPLE),
                Button("QUIT", "QUIT", cx - 150, 348, 300, 50, RED)]
    if st == gc.READY:
        return [Button("START_ROUND", "START ROUND", cx - 150, 305, 300, 56, GREEN),
                Button("MENU", "MENU", cx - 150, 378, 140, 42, GREY),
                Button("SETTINGS", "SETTINGS", cx + 10, 378, 140, 42, PURPLE)]
    if st == gc.SCORE_UPDATE:
        return [Button("NEW_GAME", "NEW GAME", 25, 415, 170, 46, YELLOW),
                Button("NEXT_ROUND", "NEXT ROUND", 215, 415, 210, 46, GREEN),
                Button("MENU", "MENU", 445, 415, 170, 46, GREY)]
    if st == gc.GAME_OVER:
        return [Button("NEW_GAME", "PLAY AGAIN", cx - 150, 300, 300, 56, GREEN),
                Button("MENU", "MENU", cx - 150, 370, 300, 46, GREY)]
    if st == gc.SETTINGS:
        out = [Button("EDIT_NAME", "EDIT", w - 250, row_y(0), 214, 36, BLUE)]
        for i in range(1, len(ROWS)):
            out.append(Button(f"ROW:{i}:-1", "<", w - 250, row_y(i), 36, 36, BLUE))
            out.append(Button(f"ROW:{i}:+1", ">", w - 72, row_y(i), 36, 36, BLUE))
        out.append(Button("BACK", "SAVE & BACK", cx - 100, row_y(len(ROWS)) + 14, 200, 46, GREEN))
        return out
    return []
