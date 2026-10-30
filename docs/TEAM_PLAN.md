# Group 24 – Team Plan (4 members)

Split by module so people rarely edit the same file. Every member also writes the tests for their own part.

| Member | Role | Files | Spec parts | Test cases (spec §16) |
|--------|------|-------|-----------|-----------------------|
| **A** | Vision lead | `camera.py`, `hand_tracker.py`, `config.py` | FR-01, FR-02, FR-03, FR-12, FR-13 (camera) | Camera, Hand, Camera Recovery, Multi-Hand, Lighting, Distance |
| **B** | Gesture lead | `gesture_classifier.py`, `gesture_stabilizer.py` | FR-04, FR-06, §7, §8 | Rock, Paper, Scissors, Unknown, Stability |
| **C** | Game logic lead | `game_controller.py`, `game_rules.py`, `computer_player.py`, `score_manager.py`, `history.py` | FR-05, FR-07–FR-11, §9, §13, §14 | Countdown, Win, Lose, Draw, Score, Duplicate, History, Reset |
| **D** | UI + docs lead | `renderer.py`, `main.py`, `audio.py`, README, diagrams, demo video | §12, FR-01 (welcome), §18 deliverables | Performance (FPS), usability (<2 min to learn) |

## Timeline (suggested, matches spec §19 phases)
| Week | A | B | C | D |
|------|---|---|---|---|
| 1 | Run webcam + landmarks on every laptop | Study landmark numbering; tune `finger_extend_ratio` | Review rules/state machine, run tests | Run the UI, list UI improvements |
| 2 | Camera-lost recovery, camera selection, primary-hand policy | Record real-hand tests (varied light/distance); fix confusions | Target score modes, history JSON save | Polish screens, add Settings screen |
| 3 | Lighting + distance + multi-hand tests | Stability tuning with real players | Edge cases; future AI "Hard" mode (optional) | Sounds/animations (optional), architecture + state diagrams |
| 4 | Fill test-results table | Fill test-results table | Fill test-results table | Demo video, final README, slides, rehearsal |

## Working rules
- One shared Git repo; each member works on a branch named after their role (`vision`, `gesture`, `logic`, `ui`) and merges through pull requests.
- Never mix classifier code and game code (spec §24).
- Before every merge: `python -m pytest` must pass.
- Weekly 20-minute sync: demo what works, list blockers.

## Deliverables checklist (spec §18)
- [x] Source code (starter provided)
- [x] Hand tracking module, gesture classifier, rule engine, computer module
- [x] Scoreboard + history, UI, requirements.txt, README
- [ ] System architecture diagram (D)
- [ ] State-flow diagram (D, from spec §9)
- [ ] Gesture guide image in `assets/images` (B + D)
- [ ] Test cases + results table (all; template below)
- [ ] Demo video / live demo (D, everyone rehearses)

## Test results template
| Test | Who | Date | Result (Pass/Fail) | Notes |
|------|-----|------|-------------------|-------|
| Camera | A | | | |
| Hand | A | | | |
| Rock | B | | | |
| Paper | B | | | |
| Scissors | B | | | |
| Unknown | B | | | |
| Countdown | C | | | |
| Win / Lose / Draw | C | | | |
| Score once per round | C | | | |
| Reset | C | | | |
| Lighting (bright/normal/dim/backlit) | A | | | |
| Distance | A | | | |
| Multi-hand | A | | | |
| Performance (FPS) | D | | | |

## Ideas for extra marks
Two-player mode (two hands, left/right of the frame), First-to-3/5 (already in `Settings.target_score`), Easy/Normal/Hard computer, sound effects, leaderboard saved to `data/game_history.json`.
