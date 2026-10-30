import json, os, random, tempfile

from src.computer_player import ComputerPlayer, predict_next, counter_to
from src.config import Settings, load_settings, save_settings
from src.settings_menu import SettingsMenu, ROWS


def share(level, history, move, n=3000, seed=1):
    cp = ComputerPlayer(random.Random(seed))
    return sum(cp.choose(history, level) == move for _ in range(n)) / n


def test_predict_needs_history_and_finds_pattern():
    assert predict_next(["ROCK", "PAPER"]) is None
    assert predict_next(["ROCK"] * 5) == "ROCK"
    # after ROCK the player always plays PAPER
    assert predict_next(["ROCK", "PAPER", "ROCK", "PAPER", "ROCK"]) == "PAPER"


def test_counter_to():
    assert counter_to("ROCK") == "PAPER"
    assert counter_to("PAPER") == "SCISSORS"
    assert counter_to("SCISSORS") == "ROCK"


def test_hard_counters_a_predictable_player():
    assert share("HARD", ["ROCK"] * 10, "PAPER") > 0.65


def test_hard_is_not_deterministic():
    assert share("HARD", ["ROCK"] * 10, "PAPER") < 0.9


def test_easy_often_loses_on_purpose():
    assert share("EASY", ["ROCK"] * 10, "SCISSORS") > 0.5


def test_normal_is_roughly_uniform():
    for m in ("ROCK", "PAPER", "SCISSORS"):
        assert abs(share("NORMAL", ["ROCK"] * 10, m) - 1 / 3) < 0.05


def test_levels_never_return_invalid_move_with_empty_history():
    cp = ComputerPlayer()
    for lvl in ("EASY", "NORMAL", "HARD"):
        assert cp.choose([], lvl) in ("ROCK", "PAPER", "SCISSORS")


def test_menu_navigation_and_changes():
    s = Settings(); m = SettingsMenu(s)
    m.handle("down")                       # Character row
    m.handle("right")
    assert s.avatar == "PANDA"
    m.handle("s"); m.handle("d")           # Level row
    assert s.difficulty == "HARD"
    m.handle("d")
    assert s.difficulty == "EASY"          # wraps around
    m.handle("down"); m.handle("right")    # Match row
    assert s.target_score == 3
    m.handle("right")
    assert s.target_score == 3              # Match length is fixed at first to 3
    m.handle("down"); m.handle("right")    # Countdown row
    assert s.countdown_seconds == 4
    m.handle("down"); m.handle("enter")    # Next round row toggles
    assert s.auto_next is True
    m.handle("down"); m.handle("enter")    # Sound row toggles
    assert s.sound is False
    m.handle("down")
    assert m.sel == 0                      # wraps to Name


def test_menu_name_editing():
    s = Settings(player_name="AB"); m = SettingsMenu(s)
    m.handle("enter")
    assert m.editing
    m.handle("C"); m.handle("backspace"); m.handle("backspace"); m.handle("Z")
    m.handle("q")                          # 'q' is typed, not quit, while editing
    assert s.player_name == "AZq"
    for ch in "abcdefghijklmnop":
        m.handle(ch)
    assert len(s.player_name) == 10
    m.handle("enter")
    assert not m.editing


def test_menu_esc_closes_and_fixes_empty_name():
    s = Settings(player_name=""); m = SettingsMenu(s)
    assert m.handle("esc") == "close"
    assert s.player_name == "PLAYER"


def test_menu_has_value_text_for_every_row():
    m = SettingsMenu(Settings())
    assert all(m.value_text(i) for i in range(len(ROWS)))


def test_settings_save_and_load_roundtrip():
    path = os.path.join(tempfile.mkdtemp(), "settings.json")
    s = Settings(player_name="Saory", avatar="FROG", difficulty="HARD", target_score=5, countdown_seconds=4, sound=False)
    save_settings(s, path)
    t = load_settings(path)
    assert (t.player_name, t.avatar, t.difficulty, t.target_score, t.countdown_seconds, t.sound) == \
        ("Saory", "FROG", "HARD", 3, 4, False)


def test_load_ignores_missing_or_broken_file():
    d = tempfile.mkdtemp()
    assert load_settings(os.path.join(d, "nope.json")).difficulty == "NORMAL"
    bad = os.path.join(d, "bad.json")
    open(bad, "w").write("{not json")
    assert load_settings(bad).player_name == "PLAYER"
    wrong = os.path.join(d, "wrong.json")
    json.dump({"difficulty": 5, "sound": "yes"}, open(wrong, "w"))
    t = load_settings(wrong)
    assert t.difficulty == "NORMAL" and t.sound is True     # wrong types are ignored
