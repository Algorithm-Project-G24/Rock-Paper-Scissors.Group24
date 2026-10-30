from src.config import Settings
from src import game_controller as gc
from src.game_controller import GameController


class Clock:
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t
    def advance(self, dt): self.t += dt


class FixedComputer:
    def __init__(self, move): self.move = move; self.calls = 0
    def choose(self, *a, **kw): self.calls += 1; return self.move


def make(computer_move="SCISSORS", **kw):
    clock = Clock()
    s = Settings(**kw)
    comp = FixedComputer(computer_move)
    return GameController(s, comp, clock), clock, comp


def run_to_capture(c, clock):
    c.start_game(); c.start_round()
    clock.advance(c.s.countdown_seconds + 0.1)
    c.update()
    assert c.state == gc.CAPTURE


def show(c, clock, gesture, frames=10):
    for _ in range(frames):
        clock.advance(0.05)
        c.update(gesture, True)


def test_full_round_win():
    c, clock, comp = make("SCISSORS")
    run_to_capture(c, clock)
    show(c, clock, "ROCK")
    assert c.state == gc.RESULT
    assert (c.player_move, c.computer_move, c.result) == ("ROCK", "SCISSORS", "WIN")
    assert (c.score.player, c.score.rounds) == (1, 1)


def test_countdown_gesture_is_ignored():
    c, clock, _ = make()
    c.start_game(); c.start_round()
    for _ in range(20):                      # shown during countdown
        clock.advance(0.05); c.update("PAPER", True)
    assert c.state == gc.COUNTDOWN and c.score.rounds == 0


def test_no_capture_before_go():
    c, clock, _ = make()
    c.start_game(); c.start_round()
    clock.advance(1.0); c.update("ROCK", True)
    assert c.state == gc.COUNTDOWN and c.player_move is None


def test_score_updates_exactly_once_and_computer_called_once():
    c, clock, comp = make()
    run_to_capture(c, clock)
    show(c, clock, "ROCK", 40)               # keep showing the gesture for a long time
    assert c.score.rounds == 1 and comp.calls == 1


def test_unknown_never_produces_result_and_times_out():
    c, clock, _ = make()
    run_to_capture(c, clock)
    show(c, clock, "UNKNOWN", 100)           # 5 s > capture_timeout
    assert c.state == gc.READY and c.score.rounds == 0 and c.result is None


def test_no_hand_shows_guidance():
    c, clock, _ = make()
    run_to_capture(c, clock)
    clock.advance(0.1); c.update("UNKNOWN", False)
    assert "hand" in c.message.lower()


def test_auto_next_round_and_new_game_reset():
    c, clock, _ = make(auto_next=True)
    run_to_capture(c, clock)
    show(c, clock, "PAPER")
    clock.advance(c.s.result_seconds + 0.1); c.update()
    assert c.state == gc.SCORE_UPDATE
    clock.advance(c.s.auto_next_seconds + 0.1); c.update()
    assert c.state == gc.COUNTDOWN
    c.new_game()
    assert c.state == gc.READY and c.score.rounds == 0 and len(c.history) == 0


def test_target_score_ends_match():
    c, clock, _ = make("SCISSORS")
    for _ in range(3):
        if c.state == gc.HOME:
            run_to_capture(c, clock)
        else:
            c.start_round(); clock.advance(c.s.countdown_seconds + 0.1); c.update()
        show(c, clock, "ROCK")
        clock.advance(c.s.result_seconds + 0.1); c.update()
        if c.state == gc.SCORE_UPDATE:
            c.s.auto_next = False
    assert c.state == gc.GAME_OVER and c.winner == "PLAYER"
    assert c.score.player == 3


def test_computer_wins_match_after_three_scoring_rounds():
    c, clock, _ = make("ROCK")
    c.start_game()
    for _ in range(3):
        c.start_round()
        clock.advance(c.s.countdown_seconds + 0.1); c.update()
        show(c, clock, "SCISSORS")
        clock.advance(c.s.result_seconds + 0.1); c.update()
    assert c.state == gc.GAME_OVER and c.winner == "COMPUTER"
    assert c.score.computer == 3


def test_exit_from_any_state():
    c, clock, _ = make()
    run_to_capture(c, clock)
    c.exit()
    assert c.state == gc.EXIT


def test_settings_open_close_returns_to_previous_state():
    c, clock, _ = make()
    c.open_settings()
    assert c.state == gc.SETTINGS
    c.close_settings()
    assert c.state == gc.HOME
    c.start_game(); c.open_settings(); c.close_settings()
    assert c.state == gc.READY


def test_settings_cannot_open_mid_round():
    c, clock, _ = make()
    run_to_capture(c, clock)
    c.open_settings()
    assert c.state == gc.CAPTURE


def test_player_moves_remembered_and_cleared():
    c, clock, _ = make()
    run_to_capture(c, clock)
    show(c, clock, "ROCK")
    assert c.player_moves == ["ROCK"]
    c.new_game()
    assert c.player_moves == []
