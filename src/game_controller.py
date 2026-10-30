"""Game Controller: the state machine from spec section 9, plus SETTINGS and a two-player mode.

States: HOME -> READY -> COUNTDOWN -> CAPTURE -> RESULT -> SCORE_UPDATE -> (COUNTDOWN | READY | GAME_OVER)
        SETTINGS can be opened from HOME / READY / GAME_OVER.  EXIT from anywhere.
Modes : "CPU"    - you vs the computer
        "FRIEND" - Player 1 (left half of the picture) vs Player 2 (right half); score "player" = P1, "computer" = P2.
Time is passed in (`clock`) so the whole flow can be unit-tested without a camera.
"""
import time

from .computer_player import ComputerPlayer
from .game_rules import decide
from .gesture_stabilizer import GestureStabilizer
from .history import RoundHistory
from .score_manager import ScoreManager
from .settings_menu import AVATARS

HOME, READY, COUNTDOWN, CAPTURE, RESULT, SCORE_UPDATE, GAME_OVER, SETTINGS, EXIT = (
    "HOME", "READY", "COUNTDOWN", "CAPTURE", "RESULT", "SCORE_UPDATE", "GAME_OVER", "SETTINGS", "EXIT")
CPU, FRIEND = "CPU", "FRIEND"


class GameController:
    def __init__(self, settings, computer=None, clock=time.monotonic):
        self.s = settings
        self.computer = computer or ComputerPlayer()
        self.clock = clock
        self.score = ScoreManager()
        self.history = RoundHistory(settings.history_size)
        make = lambda: GestureStabilizer(settings.stability_window, settings.stability_ratio, settings.stability_min_frames)
        self.stabilizer, self.stabilizer2 = make(), make()
        self.lock1 = self.lock2 = None      # moves locked in CAPTURE (stay locked until the round ends)
        self.mode = CPU
        self.state = HOME
        self.message = ""
        self.winner = None
        self.player_moves = []              # every locked P1 move this match (used by HARD level)
        self._before_settings = HOME
        self._clear_round()
        self._t = self.clock()

    # ---- names shown in the UI --------------------------------------------
    @property
    def opponent_name(self) -> str:
        return "COMPUTER" if self.mode == CPU else "FRIEND"

    @property
    def opponent_avatar(self) -> str:
        if self.mode == CPU:
            return "ROBOT"
        i = AVATARS.index(self.s.avatar) if self.s.avatar in AVATARS else 0
        return AVATARS[(i + 1) % len(AVATARS)]       # friend gets a different character

    # ---- helpers -------------------------------------------------------
    def _clear_round(self):
        self.player_move = None
        self.computer_move = None   # P2's / computer's move; generated at lock but only *shown* in RESULT
        self.result = None

    def _reset_match(self):
        self.score.reset()
        self.history.clear()
        self.player_moves = []
        self._clear_round()
        self.winner = None
        self.message = ""

    def _enter(self, state):
        self.state = state
        self._t = self.clock()

    # ---- user actions ----------------------------------------------------
    def start_game(self, mode=CPU):
        if self.state == HOME:
            self.mode = mode
            self._reset_match()
            self._enter(READY)

    def start_round(self):
        if self.state in (READY, SCORE_UPDATE):
            self._clear_round()
            self.message = ""
            self.stabilizer.reset(); self.stabilizer2.reset()
            self.lock1 = self.lock2 = None
            self._enter(COUNTDOWN)

    def new_game(self):
        if self.state in (HOME, EXIT, SETTINGS):
            return
        self._reset_match()
        self._enter(READY)

    def go_home(self):
        """Back to the main menu from anywhere (cancels a running round)."""
        if self.state not in (EXIT, SETTINGS):
            self._reset_match()
            self._enter(HOME)

    def open_settings(self):
        if self.state in (HOME, READY, GAME_OVER):
            self._before_settings = self.state
            self._enter(SETTINGS)

    def close_settings(self):
        if self.state == SETTINGS:
            self._enter(self._before_settings)

    def exit(self):
        self._enter(EXIT)

    # ---- per-frame update --------------------------------------------------
    @property
    def state_age(self) -> float:
        """Seconds spent in the current state (used for animations)."""
        return self.clock() - self._t

    @property
    def countdown_value(self) -> int:
        left = self.s.countdown_seconds - int(self.clock() - self._t)
        return max(left, 0)

    def update(self, gesture="UNKNOWN", hand_present=False, gesture2="UNKNOWN", hand2_present=False):
        """Call once per camera frame with the *raw* gestures from the classifier (gesture2 = Player 2)."""
        now = self.clock()
        elapsed = now - self._t

        if self.state == COUNTDOWN:
            # gestures shown during the countdown are ignored on purpose
            if elapsed >= self.s.countdown_seconds:
                self.stabilizer.reset(); self.stabilizer2.reset()
                self.lock1 = self.lock2 = None
                self._enter(CAPTURE)

        elif self.state == CAPTURE:
            if self.mode == CPU:
                self.message = "" if hand_present else "Show your hand"
                self.stabilizer.push(gesture if hand_present else "UNKNOWN")
                self.lock1 = self.lock1 or self.stabilizer.locked()
                if self.lock1:
                    self._finish_round(self.lock1, None)
                    return
            else:
                self.message = "" if (hand_present and hand2_present) else "Both players: show your hand"
                if not self.lock1:
                    self.stabilizer.push(gesture if hand_present else "UNKNOWN")
                    self.lock1 = self.stabilizer.locked()
                if not self.lock2:
                    self.stabilizer2.push(gesture2 if hand2_present else "UNKNOWN")
                    self.lock2 = self.stabilizer2.locked()
                if self.lock1 and self.lock2:
                    self._finish_round(self.lock1, self.lock2)
                    return
            if elapsed >= self.s.capture_timeout:
                self.message = "No valid gesture - round cancelled" if self.mode == CPU \
                    else "Both players must show a move - round cancelled"
                self._enter(READY)

        elif self.state == RESULT:
            if elapsed >= self.s.result_seconds:
                self.winner = self.score.winner(self.s.target_score)
                self._enter(GAME_OVER if self.winner else SCORE_UPDATE)

        elif self.state == SCORE_UPDATE:
            if self.s.auto_next and elapsed >= self.s.auto_next_seconds:
                self.start_round()

    def _finish_round(self, p1_move: str, p2_move=None):
        """Runs exactly once per round because the state leaves CAPTURE here."""
        self.player_move = p1_move
        self.computer_move = p2_move or self.computer.choose(self.player_moves, self.s.difficulty)
        self.player_moves.append(p1_move)
        self.result = decide(self.player_move, self.computer_move)
        self.score.record(self.result)
        self.history.add(self.player_move, self.computer_move, self.result)
        self._enter(RESULT)
