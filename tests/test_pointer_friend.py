from src import game_controller as gc
from src.config import Settings
from src.game_controller import GameController
from src.gesture_classifier import classify, is_pointing
from src.hand_tracker import split_players, primary_hand
from src.layout import buttons_for
from src.pointer_ui import Button, DwellPointer, hit_test
from tests.helpers import make_hand, ROCK, PAPER, SCISSORS

POINT = dict(index=True, middle=False, ring=False, pinky=False)


class Clock:
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t
    def advance(self, dt): self.t += dt


class FixedComputer:
    def __init__(self): self.calls = 0
    def choose(self, *a, **kw): self.calls += 1; return "ROCK"


# ---------------- pointing gesture ----------------
def test_is_pointing_only_for_index_finger():
    assert is_pointing(make_hand(POINT))
    for other in (ROCK, PAPER, SCISSORS):
        assert not is_pointing(make_hand(other))
    assert not is_pointing(None)


def test_pointing_is_not_a_game_gesture():
    assert classify(make_hand(POINT)) == "UNKNOWN"      # menu pointing never becomes a move


# ---------------- dwell pointer ----------------
def make_pointer():
    clock = Clock()
    return DwellPointer(dwell=1.0, cooldown=0.5, grace=0.2, clock=clock), clock


BTNS = [Button("A", "A", 0, 0, 100, 50), Button("B", "B", 200, 0, 100, 50)]


def test_hold_on_button_activates_once():
    p, clock = make_pointer()
    fired = []
    for _ in range(15):
        clock.advance(0.1)
        r = p.update((50, 25), BTNS)
        if r: fired.append(r)
    assert fired == ["A"]                      # once, not every frame (cooldown)


def test_no_activation_if_not_held_long_enough():
    p, clock = make_pointer()
    for _ in range(8):
        clock.advance(0.1)
        assert p.update((50, 25), BTNS) is None
    assert 0.5 < p.progress < 1.0


def test_moving_to_another_button_restarts_timer():
    p, clock = make_pointer()
    for _ in range(8):
        clock.advance(0.1); p.update((50, 25), BTNS)
    clock.advance(0.1); p.update((250, 25), BTNS)
    assert p.hover == "B" and p.progress < 0.2


def test_leaving_buttons_resets_and_short_dropout_is_forgiven():
    p, clock = make_pointer()
    for _ in range(5):
        clock.advance(0.1); p.update((50, 25), BTNS)
    clock.advance(0.1); p.update(None, BTNS)       # 0.1 s tracking dropout
    assert p.hover == "A"
    clock.advance(0.3); p.update(None, BTNS)       # long dropout
    assert p.hover is None
    clock.advance(0.1); p.update((150, 300), BTNS)  # empty space
    assert p.hover is None and p.progress == 0


def test_hit_test():
    assert hit_test(BTNS, (50, 25)).id == "A"
    assert hit_test(BTNS, (150, 25)) is None
    assert hit_test(BTNS, None) is None


# ---------------- layout ----------------
def overlap(a, b):
    return not (a.x + a.w <= b.x or b.x + b.w <= a.x or a.y + a.h <= b.y or b.y + b.h <= a.y)


def test_every_screen_has_valid_non_overlapping_buttons():
    c = GameController(Settings())
    expected = {gc.HOME: {"PLAY_CPU", "PLAY_FRIEND", "SETTINGS", "QUIT"},
                gc.READY: {"START_ROUND", "MENU", "SETTINGS"},
                gc.SCORE_UPDATE: {"NEXT_ROUND", "NEW_GAME", "MENU"},
                gc.GAME_OVER: {"NEW_GAME", "MENU"}}
    for state, ids in expected.items():
        c.state = state
        bs = buttons_for(c)
        assert {b.id for b in bs} == ids
    for state in (gc.HOME, gc.READY, gc.SCORE_UPDATE, gc.GAME_OVER, gc.SETTINGS):
        c.state = state
        bs = buttons_for(c, 640, 480)
        for i, a in enumerate(bs):
            assert 0 <= a.x and a.x + a.w <= 640 and 0 <= a.y and a.y + a.h <= 480, (state, a.id)
            for b in bs[i + 1:]:
                assert not overlap(a, b), (state, a.id, b.id)


def test_no_buttons_during_a_round():
    c = GameController(Settings())
    for state in (gc.COUNTDOWN, gc.CAPTURE, gc.RESULT):
        c.state = state
        assert buttons_for(c) == []            # a stray finger cannot cancel a round


# ---------------- hand assignment ----------------
def fake_hand(x, size=0.1):
    return ([(x, 0.5, 0)] + [(x + size * (i % 3 - 1), 0.5 - size * (i / 21), 0) for i in range(1, 21)], object())


def test_split_players_left_right():
    l, r = fake_hand(0.25), fake_hand(0.75)
    p1, p2 = split_players([r, l])
    assert p1 is l and p2 is r


def test_split_players_single_hand_and_none():
    l = fake_hand(0.3)
    assert split_players([l]) == (l, None)
    assert split_players([]) == (None, None)


def test_split_players_biggest_hand_per_side():
    small, big = fake_hand(0.2, 0.05), fake_hand(0.3, 0.2)
    p1, _ = split_players([small, big])
    assert p1 is big
    assert primary_hand([small, big]) is big


# ---------------- two-player game flow ----------------
def friend_game(**kw):
    clock = Clock()
    comp = FixedComputer()
    c = GameController(Settings(**kw), comp, clock)
    c.start_game(gc.FRIEND)
    c.start_round()
    clock.advance(c.s.countdown_seconds + 0.1)
    c.update()
    assert c.state == gc.CAPTURE
    return c, clock, comp


def frames(c, clock, g1, g2, n=10, h1=True, h2=True):
    for _ in range(n):
        clock.advance(0.05)
        c.update(g1, h1, g2, h2)


def test_friend_round_uses_both_players_and_never_the_computer():
    c, clock, comp = friend_game()
    frames(c, clock, "ROCK", "SCISSORS")
    assert c.state == gc.RESULT
    assert (c.player_move, c.computer_move, c.result) == ("ROCK", "SCISSORS", "WIN")
    assert comp.calls == 0 and c.score.rounds == 1


def test_friend_player2_can_win():
    c, clock, _ = friend_game()
    frames(c, clock, "SCISSORS", "ROCK")
    assert c.result == "LOSE" and c.score.computer == 1     # "computer" slot = player 2


def test_friend_draw():
    c, clock, _ = friend_game()
    frames(c, clock, "PAPER", "PAPER")
    assert c.result == "DRAW"


def test_friend_round_waits_for_slow_player():
    c, clock, _ = friend_game()
    frames(c, clock, "ROCK", "UNKNOWN", n=20)      # P2 not ready yet
    assert c.state == gc.CAPTURE and c.lock1 == "ROCK"
    frames(c, clock, "ROCK", "PAPER", n=10)        # P2 locks later
    assert c.state == gc.RESULT and c.result == "LOSE"


def test_friend_lock_is_sticky():
    c, clock, _ = friend_game()
    frames(c, clock, "ROCK", "UNKNOWN", n=12)
    frames(c, clock, "PAPER", "SCISSORS", n=12)    # P1 changes mind after locking: too late
    assert c.player_move == "ROCK"


def test_friend_round_cancelled_if_a_player_never_shows():
    c, clock, _ = friend_game()
    frames(c, clock, "ROCK", "UNKNOWN", n=100, h2=False)    # 5 s > capture_timeout
    assert c.state == gc.READY and c.score.rounds == 0
    assert "Both" in c.message


def test_friend_names_and_avatars():
    c = GameController(Settings(avatar="CAT"))
    c.start_game(gc.FRIEND)
    assert c.opponent_name == "FRIEND" and c.opponent_avatar != "CAT"
    c.go_home(); c.start_game(gc.CPU)
    assert c.opponent_name == "COMPUTER" and c.opponent_avatar == "ROBOT"


def test_go_home_resets_match_from_anywhere():
    c, clock, _ = friend_game()
    frames(c, clock, "ROCK", "PAPER")
    c.go_home()
    assert c.state == gc.HOME and c.score.rounds == 0 and len(c.history) == 0
