# Rock Paper Scissors – Computer Vision Game (Group 24)

Play Rock / Paper / Scissors against the computer using your hand in front of a webcam.
Built with Python, OpenCV and MediaPipe Hands.

## Install
```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```
Python 3.11 – 3.12 is recommended (MediaPipe may lag on the newest Python versions).

## Run
```bash
python main.py
```
| Key | Action |
|-----|--------|
| S / F | Play vs computer / vs friend (home screen) |
| ESC | Back to the menu (quit if already there) |
| T | Settings (name, character, level, match, countdown, sound) |
| SPACE | Start a round (rounds then continue automatically) |
| R | New game (reset score + history) |
| C | Switch camera |
| M | Mute / unmute beeps (Windows) |
| Q | Quit |

## Control the game with your hand
In every menu, **point your index finger** at a button (only the index finger up) and **hold it for about 1 second**.
A ring fills around your fingertip, then the button is pressed. Mouse clicks work too.
During a round the buttons are hidden, so a stray finger can never cancel a round.

## Play modes
| Button / key | Mode |
|---|---|
| PLAY vs COMPUTER (S) | You against the computer (levels EASY / NORMAL / HARD) |
| PLAY vs FRIEND (F) | Two players, one camera. Player 1 stands on the LEFT half of the screen, Player 2 on the RIGHT half. Each uses ONE hand. Both must lock a move; both moves are revealed together. |

## Gestures
| Gesture | Hand shape |
|---------|-----------|
| ROCK | closed fist |
| PAPER | open hand, 4 fingers up |
| SCISSORS | index + middle finger up, others folded |

Show your move **after GO**. Hold it steady for about half a second until it locks.

## Tests
```bash
python -m pytest -v
```

## Structure
`src/hand_tracker.py` (landmarks) → `gesture_classifier.py` (ROCK/PAPER/SCISSORS/UNKNOWN) → `gesture_stabilizer.py` (noise filter) → `game_controller.py` (state machine) → `game_rules.py`, `computer_player.py`, `score_manager.py`, `history.py` → `renderer.py` (UI).
The classifier knows nothing about the game, and the rule engine knows nothing about the camera, so each can be tested alone.

Tune thresholds and countdown in `src/config.py`. Matches are first to 3 scoring wins.

## Privacy
All frames are processed locally. No video is saved or uploaded.

## Settings, characters and levels
Press **T** on the home screen to open Settings. Use W/S or UP/DOWN to choose a row, A/D or LEFT/RIGHT to change it,
ENTER on *Name* to type your name, ESC to save and go back. Choices are remembered in `data/settings.json`.

| Level | Computer behaviour |
|-------|--------------------|
| EASY | Makes silly mistakes (40% of the time it plays what loses to your predicted move) |
| NORMAL | Pure random, a fair fight |
| HARD | Learns your habits from your past moves and counters them 65% of the time |

The computer never sees your current move, only your earlier ones. Characters: CAT, PANDA, FROG, ROBOT.
