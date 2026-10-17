# Food Court

An endless courtroom survival game built with Python and Pygame. Start directly in the courtroom, read Knife's argument, then click the moving fallacy label before time expires.

## Launch

Python 3.9+ is supported by this build (the project plan recommends 3.11+). In this folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

On Windows use `python` and activate with `.venv\Scripts\activate`. From another folder, use absolute paths to this environment's Python and `main.py`. Data and artwork paths resolve relative to the project.

For the existing local environment:

```sh
"/Users/boxianyu/Documents/GitHub/Food-Court-/.venv/bin/python" "/Users/boxianyu/Documents/GitHub/Food-Court-/main.py"
```

## Play

- Read without a time limit. **Ready** slides the board into view over 0.35 seconds; its completion starts the full 10-second answer timer.
- Click a moving label: +100 points if correct, -20 HP if incorrect or too late. Five mistakes end the session. No healing, bonuses, or victory condition.
- Correct answers show a 1.2-second **OBJECTION!** toward Knife. Wrong answers/timeouts show a red ribbon before revealing the explanation.
- Feedback names the correct answer, explains the reasoning, and marks targets with both text and color. **Continue** dismisses the board before the next round. The final explanation appears before **View results**.
- New fallacy cards appear during untimed reading; **Got it** dismisses the card. Read the question, then press **Ready**.
- **Play Again** resets the full session, including unlocks, counters, targets, reactions, effects, and timer. Close the window to quit at any stage.

The Chef is a neutral judge; Knife makes the argument. Neither has HP. Tomato's expression follows HP: normal at 80–100, nervous at 40–60, panic at 20 or below. The original Tomato sprite sheet is preserved. Knife uses the supplied artwork. Chef is a drawn fallback because no Chef artwork was supplied; characters also have missing-asset fallbacks. No audio is loaded, so missing sound files cannot break play.

## Progression and layout

The authoritative source is the [project plan](https://docs.google.com/document/d/1MoXh8dSYvreQXiWzX8rPt7YX2SCdHoGaBdh0ApbEiXI/edit).

Section 5.7 overrides older fixed-three-choice examples. Start with Personal Attack and Bandwagon. Unlock False Dilemma at question 6, Appeal to Pity at 11, Appeal to Irrelevant Authority at 16, Hasty Generalization at 21, Straw Man at 26, and Red Herring at 30. Subsequent categories unlock every five questions, ending with Moving the Goalposts at 80. Choice counts grow to eight, then stay capped at eight.

`data/difficulty.json` stores the exact unlock thresholds and order. The session validates it and reads it into `settings.DIFFICULTY_SCHEDULE`. Questions come only from unlocked categories. Choices include the answer once, with unique unlocked distractors. Every eligible question is used before its bag repeats; an unlock rebuilds the eligible bag, keeping the immediate-repeat guard. The bag never changes source records.

The 1280×720 courtroom uses a slim HUD, dialogue above the answer surface, Knife on the left, Tomato on the right, and Chef behind the central bench. The cutting board occupies `(280,100,720,600)`; its shared wood-only movement area is `(326,258,628,390)`. The newer presentation request overrides the original layout.

**All labels share the full answer box. There are no lanes, cells, or individual movement zones.** Initial positions are randomly packed with a reading gap while labels are hidden. After Ready, positions evolve only through integration of persistent velocity. Randomness changes smooth steering, not positions. Labels travel at varied horizontal, vertical, and diagonal angles; text stays upright.

## Editable data and settings

- `data/fallacies.json`: 18 fallacy IDs, names, definitions, and examples from Section 6.1. IDs not supplied by the document were assigned stable snake_case identifiers.
- `data/questions.json`: 36 reference examples, 15 Section 6.5 drafts, and the 10 preserved prototype drafts (61 questions). Explanations were written/adapted for gameplay because the document's example bank does not provide per-example explanations. Records include provenance in `source`. All content still needs the team's educational review, especially the older draft examples.
- Questions require a unique `id`, valid `fallacy`, `argument` of 1–220 characters, and `explanation` of 1–260 characters. Optional stored `choices` need 2–8 unique valid IDs including the answer. Live choices are generated from the current unlocked pool; stored choices cannot force locked categories into play.
- Startup validation shows a helpful filename/record error if content is invalid. Correct the JSON and restart.
- `settings.py`: scoring, damage, timer, shared answer-box geometry, motion speed, expression thresholds, objection duration, and tint duration/opacity. Set `LABEL_SPEED_MULTIPLIER = 0` for stationary targets.
- `assets/Tomato_SpriteSheet.png` is unchanged. Its five painted expressions are cropped in code; the transparent remainder is ignored.

The main loop is asynchronous, processes input before updating time, and uses delta time throughout. A valid click with positive time remaining wins its frame's timeout race. One guarded method applies score, HP, outcome counts, and feedback once. There are no new runtime dependencies beyond Pygame.

This delivery focuses on core gameplay. Tutorial, dictionary/guide, title/menu expansion, persistent high score, final character art, sound, browser packaging, and Windows/Linux verification remain outside this task. The old disabled Pause/Guide/Mute placeholders were removed rather than left as nonfunctional controls.

## Continuous shared-box motion

Each target keeps a floating-point position, velocity, heading, independent random generator, and steering clock. Random steering is filtered over time and limited by turn rate and acceleration. Nominal cruising speeds start at **28–36 px/s** for two/three choices and **18.2–23.4 px/s** for four/eight choices: twice the previous values. Speed can ease down during yielding and recover toward nominal speed.

Wall steering predicts curved trajectories including time to turn. Neighbor avoidance compares future **rectangles**, not center-distance circles. A shared velocity solver limits how fast a pair can close its current separating gap, sharing the adjustment between labels and leaving tangential motion free. Separating-face hysteresis prevents jerks at diagonal encounters. Labels delayed by congestion steer toward a clear direction. No collision is resolved by moving a label to another position.

Adjust motion in `settings.py`:

| Setting | Effect |
| --- | --- |
| `TARGET_SPEED`, `DENSE_SPEED_FACTOR` | Nominal speed and dense-group multiplier |
| `WANDER_STRENGTH`, `STEERING_CHANGE_INTERVAL` | Curvature and independent steering timing |
| `STEERING_RESPONSE`, `TURN_RESPONSE` | How gradually steering/turning changes blend in |
| `MAX_TURN_RATE`, `MAX_ANGULAR_ACCELERATION`, `MAX_ACCELERATION` | Comfortable turning and velocity changes |
| `VELOCITY_RESPONSE` | Smooth recovery toward cruising speed |
| `WALL_MARGIN`, `WALL_STRENGTH` | How early and strongly targets avoid edges |
| `TARGET_PADDING`, `TARGET_READABILITY_GAP`, `TARGET_SPAWN_GAP` | Boundary, moving-label, and initial spacing |
| `SEPARATION_LOOKAHEAD`, `SEPARATION_STRENGTH` | Predictive steering around other rectangles |
| `SEPARATION_HORIZON`, `SEPARATION_SOLVER_ITERATIONS` | Closing-speed constraints and solver precision |
| `SEPARATION_FACE_HYSTERESIS` | Stable avoidance during diagonal encounters |
| `MOTION_STEP`, `MOTION_MAX_CATCHUP` | 1/120-second simulation steps and bounded catch-up |
| `LABEL_SPEED_MULTIPLIER` | Global motion multiplier; zero freezes motion |

Normal 30, 60, and 144 FPS produce matching paths. Frames longer than the 0.1-second catch-up cap discard excess motion time rather than jumping across the box; the answer timer still follows wall time. Labels move only in ANSWERING. Hover changes appearance only. Input is checked against the exact fractional rectangle currently displayed.

The current actual-gameplay recordings are `output/answer-motion-2-choices.webp` and `output/answer-motion-8-choices.webp`, both 10-second rounds. They contain rendered game frames, not cosmetic animations. Coverage includes full-box bounds, varied angles, head-on avoidance, movement across former row boundaries, continuity, readable text, hover/click behavior, frame-rate consistency, and the original gameplay rules. Educational review and a child playtest remain useful.

## Smooth software rendering

Slow targets previously rounded their floating-point positions to whole pixels before drawing, which produced visible holds followed by one-pixel steps. Labels now use interpolated physics positions and 1/32-pixel placement. Cached premultiplied-alpha sprites blend fractional coverage without rotating, stretching, or reflowing the text. Hit detection follows the same fractional rectangle.

The desktop loop targets 120 FPS with high-resolution monotonic time and absolute frame deadlines. Steering planners have independent phase offsets to distribute their CPU work. Frame timing is measured with the actual asynchronous game loop; headless timings measure software pacing rather than the user's physical monitor/compositor. Tests include fractional visual changes, render-position interpolation, exact click edges, and movement between physics ticks. A sampled target changed its fractional display position on all 600 checked frames; the earlier integer renderer held one sampled target stationary for 478 of 600 frames. Native display feel still needs checking on the player's computer.


## Courtroom artwork and round transitions

The supplied `assets/images.jpeg` is the courtroom. Foreground pixels from the same transformed background place the Chef behind the center bench and Knife/Tomato behind the desks without seams. No Chef image was supplied, so the existing drawn Chef remains the fallback. The three reference screenshots mentioned in the request were not present in the attachments; placement follows the written composition.

`assets/Knife_SpriteSheet.png` and `assets/Tomato_SpriteSheet.png` each contain five painted expressions followed by transparent space. Runtime crops use a common canvas and fixed anchors; source files are unchanged. Knife uses frame 2 for talking, 0 for waiting, 3 (angry/frustrated) for a correct answer, and 1 (smirk) for wrong answers/timeouts. Tomato uses frames 0/2/3 for normal/nervous/panic at 80–100/40–60/0–20 HP. Character white eyes and highlights retain their source transparency.

`assets/plank-chopping-board-cartoon-illustration-vector.jpg` supplies the cutting board, rotated and scaled with its aspect ratio preserved. Only its inspected white exterior and handle opening are cut out. `LABEL_REGION` defines a shared wood-only interior, excluding the handle and curved edges. All eight choices share this surface.

Round flow: READING → BOARD_ENTER → ANSWERING → OBJECTION_ANIMATION or MISTAKE_ANIMATION → FEEDBACK → BOARD_EXIT → next round/results. Choices freeze on resolution. Continue appears after the outcome animation, and the board exits over 0.25 seconds before the next question. There is no existing pause control.

Wrong answers show a red ribbon with configurable `WRONG_BANNER_TEXT` (default `INCORRECT!`); timeout uses `TIMEOUT_BANNER_TEXT`. Banner entrance/hold/exit take 0.20/0.65/0.25 seconds, using the regular update loop. The correct-only gold OBJECTION effect remains distinct. Placement, usable board bounds, animation timing, and motion controls are in `settings.py`.

Current courtroom recordings are `output/courtroom-2-choices.webp` and `output/courtroom-8-choices.webp`. Representative rendered frames cover entrance, exit, correct, wrong, timeout, explanation, game over, and restart. Native window interaction still needs a human playtest; rendered-frame inspection and automated checks do not measure physical monitor smoothness.
