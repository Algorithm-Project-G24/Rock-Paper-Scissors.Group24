"""UI Renderer: colourful, animated OpenCV screen.

Left  = camera view with game overlays.   Right = scoreboard panel.
Everything is drawn with OpenCV shapes (no image files needed).
"""
import colorsys
import math
import random
import time

import cv2
import numpy as np

from . import game_controller as gc
from .layout import buttons_for, row_y
from .settings_menu import ROWS, LEVEL_INFO

PANEL_W = 320
FONT = cv2.FONT_HERSHEY_DUPLEX
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
GREEN, RED, YELLOW = (90, 220, 90), (80, 80, 245), (0, 225, 255)
ORANGE, PINK, SKY = (0, 150, 255), (200, 100, 255), (255, 210, 70)

RESULT_COLOR = {"WIN": GREEN, "LOSE": RED, "DRAW": YELLOW}
RESULT_TITLE = {"WIN": "YOU WIN!", "LOSE": "COMPUTER WINS!", "DRAW": "IT'S A DRAW!"}
QUIPS = {
    "WIN": ["Nice one, champ!", "Too easy!", "The computer is crying...", "Hand of steel!", "Unstoppable!"],
    "LOSE": ["Ouch! Try again!", "The robot got lucky...", "Shake it off!", "Revenge time!", "Beep boop, I win!"],
    "DRAW": ["Great minds think alike!", "Twins!", "Mirror, mirror...", "Nobody wins. Awkward."],
}
LEVEL_COLOR = {"EASY": GREEN, "NORMAL": YELLOW, "HARD": RED}
FRIEND_QUIPS = ["What a battle!", "So close!", "Rematch time!", "Epic showdown!"]
POINTER_STATES = (gc.HOME, gc.READY, gc.SCORE_UPDATE, gc.GAME_OVER, gc.SETTINGS)
GUIDE = [("ROCK", "closed fist"), ("PAPER", "open hand"), ("SCISSORS", "2 fingers up")]


# ------------------------------------------------------------------ helpers
def hue(h, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, 0.75, v)
    return int(b * 255), int(g * 255), int(r * 255)


def text(img, s, org, scale=0.7, color=WHITE, thick=1):
    cv2.putText(img, s, org, FONT, scale, BLACK, thick + 3, cv2.LINE_AA)
    cv2.putText(img, s, org, FONT, scale, color, thick, cv2.LINE_AA)


def ctext(img, s, cy, scale=0.8, color=WHITE, thick=1, cx=None):
    (w, h), _ = cv2.getTextSize(s, FONT, scale, thick)
    cx = img.shape[1] // 2 if cx is None else cx
    text(img, s, (cx - w // 2, int(cy + h // 2)), scale, color, thick)


def rainbow(img, s, cy, scale, t, thick=3, cx=None, bounce=8):
    widths = [cv2.getTextSize(c, FONT, scale, thick)[0][0] + 2 for c in s]
    x = (img.shape[1] // 2 if cx is None else cx) - sum(widths) // 2
    for i, c in enumerate(s):
        y = int(cy + math.sin(t * 5 + i * 0.6) * bounce)
        text(img, c, (x, y), scale, hue(t * 0.5 + i * 0.07), thick)
        x += widths[i]


def tint(view, color, alpha):
    return cv2.addWeighted(view, 1 - alpha, np.full_like(view, color), alpha, 0)


def _face(img, cx, cy, r, mood):
    for sx in (-1, 1):
        ex, ey = int(cx + sx * 0.3 * r), int(cy - 0.12 * r)
        cv2.circle(img, (ex, ey), max(3, int(0.15 * r)), WHITE, -1)
        cv2.circle(img, (ex, ey), max(3, int(0.15 * r)), BLACK, 2)
        cv2.circle(img, (ex + int(0.03 * r), ey + int(0.02 * r)), max(2, int(0.07 * r)), BLACK, -1)
    if mood == "happy":
        cv2.ellipse(img, (cx, int(cy + 0.2 * r)), (int(0.22 * r), int(0.15 * r)), 0, 0, 180, BLACK, 3, cv2.LINE_AA)
    elif mood == "sad":
        cv2.ellipse(img, (cx, int(cy + 0.42 * r)), (int(0.2 * r), int(0.13 * r)), 0, 180, 360, BLACK, 3, cv2.LINE_AA)
    else:
        cv2.line(img, (int(cx - 0.18 * r), int(cy + 0.3 * r)), (int(cx + 0.18 * r), int(cy + 0.3 * r)), BLACK, 3, cv2.LINE_AA)


def draw_icon(img, move, cx, cy, r, mood="happy"):
    """Cartoon ROCK / PAPER / SCISSORS badge (or '?' for anything else)."""
    if move == "ROCK":
        cv2.circle(img, (cx, cy), r, (115, 120, 145), -1)
        cv2.circle(img, (cx - int(.45 * r), cy - int(.45 * r)), int(.22 * r), (170, 175, 200), -1)
        for dx, dy in ((.55, -.35), (.45, .6), (-.6, .45)):
            cv2.circle(img, (cx + int(dx * r), cy + int(dy * r)), int(.1 * r), (85, 90, 110), -1)
        _face(img, cx, cy + int(.1 * r), r, mood)
    elif move == "PAPER":
        cv2.circle(img, (cx, cy), r, (255, 190, 90), -1)
        x1, y1, x2, y2 = cx - int(.58 * r), cy - int(.72 * r), cx + int(.58 * r), cy + int(.72 * r)
        cv2.rectangle(img, (x1, y1), (x2, y2), WHITE, -1)
        fold = int(.3 * r)
        cv2.fillPoly(img, [np.array([(x2 - fold, y1), (x2, y1 + fold), (x2 - fold, y1 + fold)])], (200, 200, 210))
        for k in range(2):
            yy = y2 - int((.18 + .15 * k) * r)
            cv2.line(img, (x1 + int(.15 * r), yy), (x2 - int(.15 * r), yy), (230, 150, 70), 2)
        _face(img, cx, cy - int(.05 * r), r * .9, mood)
    elif move == "SCISSORS":
        cv2.circle(img, (cx, cy), r, (170, 110, 255), -1)
        pivot = (cx, cy + int(.15 * r))
        th = max(4, r // 6)
        for sx in (-1, 1):
            cv2.line(img, pivot, (cx + sx * int(.5 * r), cy - int(.8 * r)), (235, 235, 240), th, cv2.LINE_AA)
            cv2.line(img, pivot, (cx + sx * int(.5 * r), cy - int(.8 * r)), (160, 160, 170), 1, cv2.LINE_AA)
            cv2.circle(img, (cx - sx * int(.32 * r), cy + int(.58 * r)), int(.24 * r), (60, 60, 235), max(3, th // 2 + 1), cv2.LINE_AA)
        cv2.circle(img, pivot, max(3, int(.09 * r)), (60, 60, 60), -1)
        for sx in (-1, 1):   # little eyes between the blades
            e = (cx + sx * int(.14 * r), cy - int(.3 * r))
            cv2.circle(img, e, max(3, int(.1 * r)), WHITE, -1)
            cv2.circle(img, e, max(2, int(.045 * r)), BLACK, -1)
    else:
        cv2.circle(img, (cx, cy), r, (130, 130, 130), -1)
        ctext(img, "?", cy, r / 25, WHITE, 3, cx)
    cv2.circle(img, (cx, cy), r, WHITE, 3, cv2.LINE_AA)


def _mouth(img, cx, cy, r, mood, color=BLACK):
    if mood == "happy":
        cv2.ellipse(img, (cx, cy), (int(.22 * r), int(.14 * r)), 0, 0, 180, color, 3, cv2.LINE_AA)
    elif mood == "sad":
        cv2.ellipse(img, (cx, cy + int(.14 * r)), (int(.2 * r), int(.12 * r)), 0, 180, 360, color, 3, cv2.LINE_AA)
    else:
        cv2.line(img, (cx - int(.16 * r), cy), (cx + int(.16 * r), cy), color, 3, cv2.LINE_AA)


def _eyes(img, cx, cy, r, dx=.32, rad=.15):
    for sx in (-1, 1):
        e = (cx + sx * int(dx * r), cy)
        cv2.circle(img, e, max(3, int(rad * r)), WHITE, -1)
        cv2.circle(img, e, max(3, int(rad * r)), BLACK, 2)
        cv2.circle(img, (e[0] + int(.03 * r), e[1] + int(.02 * r)), max(2, int(.07 * r)), BLACK, -1)


def draw_avatar(img, kind, cx, cy, r, mood="happy"):
    """The character that represents a player: CAT, PANDA, FROG or ROBOT."""
    if kind == "CAT":
        for sx in (-1, 1):
            outer = np.array([(cx + sx * int(.85 * r), cy - int(.2 * r)), (cx + sx * int(.75 * r), cy - int(1.1 * r)),
                              (cx + sx * int(.2 * r), cy - int(.85 * r))])
            inner = np.array([(cx + sx * int(.72 * r), cy - int(.4 * r)), (cx + sx * int(.68 * r), cy - int(.85 * r)),
                              (cx + sx * int(.38 * r), cy - int(.7 * r))])
            cv2.fillPoly(img, [outer], (40, 150, 250))
            cv2.fillPoly(img, [inner], (190, 170, 255))
        cv2.circle(img, (cx, cy), r, (40, 150, 250), -1)
        _eyes(img, cx, cy - int(.12 * r), r)
        cv2.fillPoly(img, [np.array([(cx - int(.08 * r), cy + int(.08 * r)), (cx + int(.08 * r), cy + int(.08 * r)), (cx, cy + int(.18 * r))])], (170, 120, 255))
        _mouth(img, cx, cy + int(.3 * r), r * .8, mood)
        for sx in (-1, 1):
            for dy in (-.04, .08):
                cv2.line(img, (cx + sx * int(.45 * r), cy + int((.22 + dy) * r)), (cx + sx * int(.95 * r), cy + int((.18 + dy * 2) * r)), WHITE, 1, cv2.LINE_AA)
    elif kind == "PANDA":
        for sx in (-1, 1):
            cv2.circle(img, (cx + sx * int(.7 * r), cy - int(.75 * r)), int(.3 * r), (35, 35, 35), -1)
        cv2.circle(img, (cx, cy), r, (250, 250, 250), -1)
        for sx in (-1, 1):
            cv2.ellipse(img, (cx + sx * int(.33 * r), cy - int(.1 * r)), (int(.2 * r), int(.27 * r)), sx * 25, 0, 360, (35, 35, 35), -1)
            e = (cx + sx * int(.33 * r), cy - int(.12 * r))
            cv2.circle(img, e, max(3, int(.11 * r)), WHITE, -1)
            cv2.circle(img, (e[0] + int(.02 * r), e[1] + int(.02 * r)), max(2, int(.05 * r)), BLACK, -1)
        cv2.ellipse(img, (cx, cy + int(.15 * r)), (int(.11 * r), int(.07 * r)), 0, 0, 360, (35, 35, 35), -1)
        _mouth(img, cx, cy + int(.3 * r), r * .8, mood)
    elif kind == "FROG":
        for sx in (-1, 1):
            cv2.circle(img, (cx + sx * int(.5 * r), cy - int(.78 * r)), int(.33 * r), (80, 200, 90), -1)
        cv2.circle(img, (cx, cy), r, (80, 200, 90), -1)
        for sx in (-1, 1):
            e = (cx + sx * int(.5 * r), cy - int(.78 * r))
            cv2.circle(img, e, int(.25 * r), WHITE, -1)
            cv2.circle(img, e, int(.25 * r), BLACK, 2)
            cv2.circle(img, (e[0], e[1] + int(.03 * r)), max(2, int(.1 * r)), BLACK, -1)
            cv2.circle(img, (cx + sx * int(.62 * r), cy + int(.2 * r)), int(.13 * r), (150, 150, 255), -1)
        cv2.circle(img, (cx - int(.08 * r), cy - int(.1 * r)), max(1, int(.03 * r)), (30, 100, 40), -1)
        cv2.circle(img, (cx + int(.08 * r), cy - int(.1 * r)), max(1, int(.03 * r)), (30, 100, 40), -1)
        _mouth(img, cx, cy + int(.35 * r), r * 1.5, mood, (30, 90, 40))
    elif kind == "ROBOT":
        cv2.line(img, (cx, cy - int(.7 * r)), (cx, cy - int(1.05 * r)), (200, 200, 200), 3)
        cv2.circle(img, (cx, cy - int(1.08 * r)), max(3, int(.12 * r)), RED, -1)
        cv2.rectangle(img, (cx - int(.85 * r), cy - int(.7 * r)), (cx + int(.85 * r), cy + int(.75 * r)), (195, 190, 185), -1)
        for sx in (-1, 1):
            c = (cx + sx * int(.4 * r), cy - int(.2 * r))
            cv2.rectangle(img, (c[0] - int(.2 * r), c[1] - int(.17 * r)), (c[0] + int(.2 * r), c[1] + int(.17 * r)), (40, 40, 40), -1)
            cv2.rectangle(img, (c[0] - int(.12 * r), c[1] - int(.1 * r)), (c[0] + int(.12 * r), c[1] + int(.1 * r)), (255, 230, 80), -1)
        _mouth(img, cx, cy + int(.38 * r), r, mood, (40, 40, 40))
        cv2.rectangle(img, (cx - int(.85 * r), cy - int(.7 * r)), (cx + int(.85 * r), cy + int(.75 * r)), WHITE, 3)
        return
    cv2.circle(img, (cx, cy), r, WHITE, 3, cv2.LINE_AA)


class Confetti:
    def __init__(self):
        self.p = []

    def burst(self, w, h, n=90):
        for _ in range(n):
            a = random.uniform(math.pi * 1.1, math.pi * 1.9)
            sp = random.uniform(6, 16)
            self.p.append([w / 2, h * 0.55, math.cos(a) * sp, math.sin(a) * sp,
                           hue(random.random()), random.randint(4, 8), random.random() * 6])

    def rain(self, w, n=3):
        for _ in range(n):
            self.p.append([random.uniform(0, w), -10, random.uniform(-1, 1), random.uniform(3, 7),
                           hue(random.random()), random.randint(4, 8), random.random() * 6])

    def draw(self, img):
        h, w = img.shape[:2]
        alive = []
        for q in self.p:
            q[0] += q[2]; q[1] += q[3]; q[3] += 0.35; q[2] *= 0.99; q[6] += 0.3
            if q[1] < h + 20:
                s = q[5]
                dx = int(math.cos(q[6]) * s)
                cv2.rectangle(img, (int(q[0]) - dx, int(q[1]) - s // 2), (int(q[0]) + dx, int(q[1]) + s // 2), q[4], -1)
                alive.append(q)
        self.p = alive[-400:]


# ------------------------------------------------------------------ renderer
class Renderer:
    def __init__(self):
        self.confetti = Confetti()
        self.events = []             # ("reveal", "WIN") ... main.py turns them into sounds
        self._prev_state = None
        self._burst_done = False
        self._shake_start = 0.0
        self._panel_bg = {}

    # ---- side panel --------------------------------------------------
    def _bg(self, h):
        if h not in self._panel_bg:
            top, bot = np.array((125, 45, 95), float), np.array((45, 20, 30), float)
            k = np.linspace(0, 1, h)[:, None, None]
            col = (top * (1 - k) + bot * k).astype(np.uint8)
            self._panel_bg[h] = np.repeat(col, PANEL_W, axis=1)
        return self._panel_bg[h].copy()

    def _panel(self, h, ctrl, fps, t, muted):
        p = self._bg(h)
        rainbow(p, "SCOREBOARD", 32, 0.75, t, 2, cx=PANEL_W // 2, bounce=3)
        sc = ctrl.score
        total = max(sc.rounds, 1)
        for i, (name, val, col) in enumerate(((ctrl.s.player_name[:10].upper(), sc.player, GREEN), (ctrl.opponent_name, sc.computer, RED), ("DRAWS", sc.draws, YELLOW))):
            y = 62 + i * 50
            text(p, f"{name}", (16, y + 12), 0.55, WHITE, 1)
            text(p, f"{val}", (PANEL_W - 50, y + 14), 0.9, col, 2)
            cv2.rectangle(p, (16, y + 22), (PANEL_W - 16, y + 34), (60, 30, 50), -1)
            cv2.rectangle(p, (16, y + 22), (16 + int((PANEL_W - 32) * val / total), y + 34), col, -1)
            cv2.rectangle(p, (16, y + 22), (PANEL_W - 16, y + 34), WHITE, 1)
        tgt = ctrl.s.target_score
        text(p, f"Round {sc.rounds + (1 if ctrl.state in (gc.COUNTDOWN, gc.CAPTURE) else 0)} | " +
             (f"First to {tgt}" if tgt else "Free play") + f" | {ctrl.s.difficulty if ctrl.mode == gc.CPU else 'VS FRIEND'}", (16, 232), 0.45, (230, 230, 230), 1)
        recent = ctrl.history.recent()
        streak = 0
        for r in recent:
            if r["result"] != "WIN":
                break
            streak += 1
        if streak >= 3:
            ctext(p, f"ON FIRE x{streak}!", 262, 0.8, hue(0.05 + 0.05 * math.sin(t * 12), 1), 2, PANEL_W // 2)
        text(p, "HISTORY", (16, 292), 0.6, YELLOW, 1)
        for i, r in enumerate(recent[:5]):
            y = 304 + i * 25
            col = RESULT_COLOR[r["result"]]
            cv2.rectangle(p, (14, y), (PANEL_W - 14, y + 21), tuple(int(c * .35) for c in col), -1)
            cv2.rectangle(p, (14, y), (14 + 6, y + 21), col, -1)
            text(p, f"{r['player'].title()} vs {r['computer'].title()}", (28, y + 16), 0.45, WHITE, 1)
            text(p, r["result"], (PANEL_W - 70, y + 16), 0.45, col, 1)
        text(p, "R new  C cam  M mute  Q quit", (16, h - 34), 0.42, (230, 230, 230), 1)
        text(p, f"FPS {fps:4.1f}" + ("   (muted)" if muted else ""), (16, h - 12), 0.45, (200, 200, 200), 1)
        return p

    # ---- main entry --------------------------------------------------
    def render(self, frame, ctrl, gesture="UNKNOWN", fps=0.0, camera_ok=True, muted=False, menu=None,
               pointer=None, pointer_pos=None):
        t = time.time()
        h, w = frame.shape[:2]
        view = frame.copy()
        st, age = ctrl.state, ctrl.state_age
        revealed = st != gc.RESULT or age >= 0.8

        if st != self._prev_state:
            if st == gc.RESULT:
                self._burst_done = False
                if ctrl.result == "LOSE" and ctrl.mode == gc.CPU:
                    self._shake_start = t
            self._prev_state = st
        if st == gc.RESULT and revealed and not self._burst_done:
            self._burst_done = True
            self.events.append(("reveal", ctrl.result))
            if ctrl.result in ("WIN", "DRAW") or ctrl.mode == gc.FRIEND:
                self.confetti.burst(w, h, 40 if ctrl.result == "DRAW" else 110)

        if not camera_ok:
            view = tint(view, (40, 20, 80), 0.6)
            ctext(view, "CAMERA LOST", h // 2 - 20, 1.4, RED, 3)
            ctext(view, "reconnecting...", h // 2 + 30, 0.8, WHITE, 2)
        elif st == gc.SETTINGS:
            self._settings(view, ctrl, menu, t)
        elif st == gc.HOME:
            self._home(view, ctrl, t)
        elif st == gc.READY:
            self._ready(view, ctrl, t)
        elif st == gc.COUNTDOWN:
            self._countdown(view, ctrl, t)
        elif st == gc.CAPTURE:
            self._capture(view, ctrl, gesture, age, t)
        elif st in (gc.RESULT, gc.SCORE_UPDATE):
            self._result(view, ctrl, revealed, age, t)
        elif st == gc.GAME_OVER:
            self._game_over(view, ctrl, t)

        if st == gc.GAME_OVER and (ctrl.winner == "PLAYER" or ctrl.mode == gc.FRIEND) and random.random() < 0.9:
            self.confetti.rain(w)
        self.confetti.draw(view)
        if st in POINTER_STATES:
            self._draw_buttons(view, buttons_for(ctrl, w, h), pointer)
            if pointer_pos is not None:
                self._draw_cursor(view, pointer_pos, pointer.progress if pointer else 0.0)

        if t - self._shake_start < 0.6 and st in (gc.RESULT, gc.SCORE_UPDATE):
            dx = int(math.sin((t - self._shake_start) * 60) * 12 * (1 - (t - self._shake_start) / 0.6))
            view = np.roll(view, dx, axis=1)

        return np.hstack([view, self._panel(h, ctrl, fps, t, muted)])

    # ---- buttons + cursor ---------------------------------------------------
    def _draw_buttons(self, v, buttons, pointer):
        for b in buttons:
            hov = pointer is not None and pointer.hover == b.id
            dark = tuple(int(c * (0.55 if not hov else 0.8)) for c in b.color)
            cv2.rectangle(v, (b.x, b.y), (b.x + b.w, b.y + b.h), dark, -1)
            if hov:
                cv2.rectangle(v, (b.x, b.y), (b.x + int(b.w * pointer.progress), b.y + b.h), b.color, -1)
            cv2.rectangle(v, (b.x, b.y), (b.x + b.w, b.y + b.h), YELLOW if hov else WHITE, 3 if hov else 2)
            scale = min(0.9, b.h / 52.0)
            while cv2.getTextSize(b.label, FONT, scale, 2)[0][0] > b.w - 14 and scale > 0.3:
                scale -= 0.05
            ctext(v, b.label, b.y + b.h // 2, scale, WHITE, 2, b.x + b.w // 2)

    def _draw_cursor(self, v, pos, progress):
        cv2.circle(v, pos, 11, BLACK, -1)
        cv2.circle(v, pos, 8, YELLOW, -1)
        cv2.ellipse(v, pos, (22, 22), -90, 0, int(360 * progress), GREEN, 5, cv2.LINE_AA)
        cv2.circle(v, pos, 22, WHITE, 1, cv2.LINE_AA)

    def _names(self, ctrl):
        return ctrl.s.player_name[:10].upper(), ctrl.opponent_name[:10].upper()

    def _title(self, ctrl):
        if ctrl.mode == gc.CPU:
            return RESULT_TITLE[ctrl.result]
        p1, p2 = self._names(ctrl)
        return {"WIN": f"{p1} WINS!", "LOSE": f"{p2} WINS!", "DRAW": "IT'S A DRAW!"}[ctrl.result]

    # ---- screens -----------------------------------------------------
    def _home(self, v, ctrl, t):
        h, w = v.shape[:2]
        v[:] = tint(v, (110, 30, 90), 0.62)
        rainbow(v, "ROCK PAPER", 66, 1.4, t, 4)
        rainbow(v, "SCISSORS", 118, 1.4, t + 1, 4)
        draw_avatar(v, ctrl.s.avatar, 52, 58 + int(math.sin(t * 4) * 4), 34)
        ctext(v, ctrl.s.player_name[:10], 108, 0.5, WHITE, 1, 52)
        lv = ctrl.s.difficulty
        ctext(v, f"LEVEL: {lv}", 40, 0.5, LEVEL_COLOR[lv], 1, w - 80)
        ctext(v, "Point your index finger at a button and hold it (or click)", 436, 0.5, WHITE, 1)
        ctext(v, "Keys: S = vs computer   F = vs friend   T = settings   Q = quit", 460, 0.42, (220, 220, 220), 1)

    def _ready(self, v, ctrl, t):
        h, w = v.shape[:2]
        v[:] = tint(v, (90, 40, 60), 0.25)
        ctext(v, "Ready to rumble?", 40, 1.0, YELLOW, 2)
        if ctrl.mode == gc.CPU:
            ctext(v, "Point at START ROUND (or press SPACE)", 80, 0.55, WHITE, 1)
            for i, m in enumerate(("ROCK", "PAPER", "SCISSORS")):
                cx, cy = 130 + i * 190, 180 + int(math.sin(t * 4 + i * 2) * 6)
                draw_icon(v, m, cx, cy, 42, "happy")
                ctext(v, GUIDE[i][0], 242, 0.55, hue(i * .3 + .05), 2, cx)
                ctext(v, GUIDE[i][1], 262, 0.45, WHITE, 1, cx)
        else:
            p1, p2 = self._names(ctrl)
            ctext(v, "Stand side by side - each player uses ONE hand", 80, 0.55, WHITE, 1)
            cv2.line(v, (w // 2, 100), (w // 2, h), WHITE, 2)
            for cx, av, name, side in ((w // 4, ctrl.s.avatar, p1, "LEFT side"), (3 * w // 4, ctrl.opponent_avatar, p2, "RIGHT side")):
                draw_avatar(v, av, cx, 175 + int(math.sin(t * 4 + cx) * 5), 46)
                ctext(v, name, 245, 0.7, YELLOW, 2, cx)
                ctext(v, side, 268, 0.5, WHITE, 1, cx)
        if ctrl.message:
            ctext(v, ctrl.message, 292, 0.6, RED, 2)

    def _countdown(self, v, ctrl, t):
        h, w = v.shape[:2]
        v[:] = tint(v, (80, 30, 60), 0.35)
        if ctrl.mode == gc.FRIEND:
            cv2.line(v, (w // 2, 90), (w // 2, h), WHITE, 2)
        n = max(ctrl.countdown_value, 1)
        frac = ctrl.state_age % 1.0
        col = (RED, ORANGE, YELLOW, GREEN)[min(n, 3) - 1] if n <= 3 else SKY
        scale = 4.2 + 1.6 * (1 - frac) ** 2
        cv2.ellipse(v, (w // 2, h // 2), (150, 150), -90, 0, int(360 * (1 - frac)), col, 12, cv2.LINE_AA)
        ctext(v, str(n), h // 2, scale, col, 10)
        ctext(v, "Get your hand ready!", 50, 0.9, WHITE, 2)

    def _capture(self, v, ctrl, gesture, age, t):
        h, w = v.shape[:2]
        if age < 0.7:
            v[:] = tint(v, (0, 200, 120), 0.35 * (1 - age / 0.7))
            ctext(v, "GO!", h // 2, 5.5 - 2 * age, hue(t), 12)
        rainbow(v, "SHOW YOUR MOVE!", 48, 1.1, t, 3)
        left = max(0.0, 1 - age / ctrl.s.capture_timeout)
        cv2.rectangle(v, (40, 70), (w - 40, 84), (50, 30, 50), -1)
        cv2.rectangle(v, (40, 70), (40 + int((w - 80) * left), 84), ORANGE if left < .35 else SKY, -1)
        cv2.rectangle(v, (40, 70), (w - 40, 84), WHITE, 1)
        if ctrl.message:
            ctext(v, ctrl.message, 120, 0.8, RED, 2)
        if ctrl.mode == gc.CPU:
            seeing = ctrl.stabilizer.current() or (gesture if gesture != "UNKNOWN" else None)
            draw_icon(v, seeing or "?", 90, h - 80, 46, "happy")
            text(v, f"I see: {seeing or '...'}", (150, h - 85), 0.8, YELLOW, 2)
            prog = ctrl.stabilizer.progress()
            cv2.rectangle(v, (150, h - 70), (w - 50, h - 52), (50, 30, 50), -1)
            cv2.rectangle(v, (150, h - 70), (150 + int((w - 200) * prog), h - 52), GREEN, -1)
            cv2.rectangle(v, (150, h - 70), (w - 50, h - 52), WHITE, 1)
            text(v, "hold still to lock it in", (150, h - 32), 0.5, WHITE, 1)
            return
        cv2.line(v, (w // 2, 90), (w // 2, h), WHITE, 2)
        for stab, lock, name, x0 in ((ctrl.stabilizer, ctrl.lock1, self._names(ctrl)[0], 0),
                                     (ctrl.stabilizer2, ctrl.lock2, self._names(ctrl)[1], w // 2)):
            seen = lock or stab.current()
            draw_icon(v, seen or "?", x0 + 50, h - 62, 32, "happy")
            text(v, f"{name[:7]}: {'LOCKED!' if lock else (seen or '...')}", (x0 + 92, h - 70), 0.5, GREEN if lock else YELLOW, 1)
            bar_w = w // 2 - 112
            prog = 1.0 if lock else stab.progress()
            cv2.rectangle(v, (x0 + 92, h - 58), (x0 + 92 + bar_w, h - 44), (50, 30, 50), -1)
            cv2.rectangle(v, (x0 + 92, h - 58), (x0 + 92 + int(bar_w * prog), h - 44), GREEN, -1)
            cv2.rectangle(v, (x0 + 92, h - 58), (x0 + 92 + bar_w, h - 44), WHITE, 1)

    def _result(self, v, ctrl, revealed, age, t):
        h, w = v.shape[:2]
        res = ctrl.result
        friend = ctrl.mode == gc.FRIEND
        v[:] = tint(v, RESULT_COLOR[res], 0.38)
        v[:] = tint(v, BLACK, 0.25)
        rm = {"WIN": ("happy", "sad"), "LOSE": ("sad", "happy"), "DRAW": ("neutral", "neutral")}[res]
        p1, p2 = self._names(ctrl)
        if revealed:
            bounce = int(abs(math.sin(t * 6)) * 14)
            py = 235 - (bounce if res == "WIN" else 0)
            cy2 = 235 - (bounce if res == "LOSE" else 0)
            draw_icon(v, ctrl.player_move, 150, py, 85, rm[0])
            draw_icon(v, ctrl.computer_move, w - 150, cy2, 85, rm[1])
            rainbow(v, self._title(ctrl), 72, 1.7 if (res != "LOSE" and not friend) else 1.3, t, 4, bounce=6)
            quips = FRIEND_QUIPS if friend else QUIPS[res]
            ctext(v, quips[ctrl.score.rounds % len(quips)], 395, 0.85, WHITE, 2)
            draw_avatar(v, ctrl.s.avatar, 62, 150, 36, rm[0])
            draw_avatar(v, ctrl.opponent_avatar, w - 62, 150, 36, rm[1])
        elif friend:
            draw_icon(v, "?", 150, 235, 85, "neutral")
            draw_icon(v, "?", w - 150, 235, 85, "neutral")
            ctext(v, "Both moves locked... reveal!", 72, 1.0, YELLOW, 2)
        else:
            draw_icon(v, ctrl.player_move, 150, 235, 85, "neutral")
            shown = ("ROCK", "PAPER", "SCISSORS")[int(age * 12) % 3]
            draw_icon(v, shown, w - 150, 235, 85, "neutral")
            ctext(v, "Computer is choosing...", 72, 1.0, YELLOW, 2)
        ctext(v, "VS", 235, 1.5, YELLOW, 4)
        ctext(v, p1, 345, 0.9, GREEN, 2, 150)
        ctext(v, p2, 345, 0.9, RED, 2, w - 150)
        if ctrl.state == gc.SCORE_UPDATE and ctrl.s.auto_next:
            ctext(v, "Next round coming... get ready!", 470, 0.5, SKY, 1)

    def _settings(self, v, ctrl, menu, t):
        h, w = v.shape[:2]
        v[:] = tint(v, (110, 35, 90), 0.8)
        s = ctrl.s
        rainbow(v, "SETTINGS", 44, 1.2, t, 3, cx=w // 2 - 60)
        draw_avatar(v, s.avatar, w - 70, 46 + int(math.sin(t * 5) * 4), 28)
        ctext(v, LEVEL_INFO[s.difficulty], 78, 0.5, LEVEL_COLOR[s.difficulty], 1, w // 2 - 60)
        if menu is None:
            return
        for i, label in enumerate(ROWS):
            y = row_y(i)
            sel = i == menu.sel
            if sel:
                cv2.rectangle(v, (24, y - 3), (w - 24, y + 39), (150, 70, 120), -1)
                cv2.rectangle(v, (24, y - 3), (w - 24, y + 39), WHITE, 2)
            text(v, label, (40, y + 26), 0.7, YELLOW if sel else WHITE, 2 if sel else 1)
            val = menu.value_text(i)
            col = LEVEL_COLOR.get(val, SKY) if i == 2 else (GREEN if val in ("ON", "AUTO") else RED if val == "OFF" else WHITE)
            if i == 0:
                text(v, val, (170, y + 26), 0.75, col, 2)
            else:
                ctext(v, val, y + 18, 0.7, col, 2, w - 161)
        hint = "Type your name, ENTER = done" if menu.editing else "Point at < > to change   |   keyboard: W/S A/D ENTER ESC"
        ctext(v, hint, 466, 0.45, WHITE, 1)

    def _game_over(self, v, ctrl, t):
        h, w = v.shape[:2]
        friend = ctrl.mode == gc.FRIEND
        win = ctrl.winner == "PLAYER"
        v[:] = tint(v, GREEN if (win or friend) else RED, 0.35)
        v[:] = tint(v, BLACK, 0.3)
        p1, p2 = self._names(ctrl)
        if friend:
            title = f"{p1 if win else p2} WINS THE MATCH!"
            tag = "What a great match!"
        else:
            title = "YOU WON THE MATCH!" if win else "COMPUTER WINS"
            tag = "The robot cannot beat a human!" if win else "Practice makes perfect!"
        rainbow(v, title, 110, 1.3 if friend else (1.5 if win else 1.6), t, 4)
        ctext(v, f"Final score   {ctrl.score.player} - {ctrl.score.computer}", 190, 1.1, YELLOW, 2)
        ctext(v, tag, 245, 0.8, WHITE, 2)
