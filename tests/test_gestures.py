import pytest
from src.gesture_classifier import classify
from src.gesture_stabilizer import GestureStabilizer
from tests.helpers import make_hand, ROCK, PAPER, SCISSORS


@pytest.mark.parametrize("deg", [0, 30, 90, 180, 270])
def test_classify_any_rotation(deg):
    assert classify(make_hand(ROCK, deg)) == "ROCK"
    assert classify(make_hand(PAPER, deg)) == "PAPER"
    assert classify(make_hand(SCISSORS, deg)) == "SCISSORS"


def test_unknown_cases():
    one_finger = dict(ROCK, index=True)
    assert classify(make_hand(one_finger)) == "UNKNOWN"
    three = dict(PAPER, pinky=False)
    assert classify(make_hand(three)) == "UNKNOWN"
    assert classify(None) == "UNKNOWN"
    assert classify([(0, 0)] * 5) == "UNKNOWN"


def test_stabilizer_needs_agreement():
    st = GestureStabilizer(window=10, ratio=0.7, min_frames=6)
    for _ in range(3):
        st.push("ROCK")
    assert st.locked() is None          # not enough frames yet
    for _ in range(5):
        st.push("ROCK")
    assert st.locked() == "ROCK"


def test_stabilizer_ignores_noise():
    st = GestureStabilizer(window=10, ratio=0.7, min_frames=6)
    for g in ["PAPER"] * 8 + ["ROCK", "UNKNOWN"]:
        st.push(g)
    assert st.locked() == "PAPER"


def test_stabilizer_rejects_flapping_and_unknown():
    st = GestureStabilizer(window=10, ratio=0.7, min_frames=6)
    for g in ["ROCK", "PAPER"] * 5:
        st.push(g)
    assert st.locked() is None
    st.reset()
    for _ in range(10):
        st.push("UNKNOWN")
    assert st.locked() is None


def test_stabilizer_progress_bar():
    st = GestureStabilizer(window=10, ratio=0.7, min_frames=6)
    assert st.progress() == 0.0
    for _ in range(3):
        st.push("PAPER")
    assert 0 < st.progress() < 1
    for _ in range(7):
        st.push("PAPER")
    assert st.progress() == 1.0
