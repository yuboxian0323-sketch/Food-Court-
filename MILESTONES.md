# Food Court coding milestones

Status: core courtroom gameplay is implemented under the revised gameplay-only request: progression, moving targets, objection, reactions, and mistake tint are now included. Tutorial/guide/menu expansion, persistence, final artwork/audio, educational review, and wider release verification remain pending. The original milestones below are retained as planning context; see README.md for the current implementation and verification status.

Based on the supplied Food Court project plan. The repository currently contains a README and Tomato sprite sheet. Each milestone builds on the previous one and ends with a playable, verifiable result. These are implementation checkpoints, not calendar estimates.

## Working specification

- Python + Pygame desktop game, 1280 x 720, targeting 60 FPS.
- Tomato is the defendant; kitchen gadgets present arguments; Chef is the neutral judge. Only Tomato has HP.
- Endless survival: 100 starting HP, +100 per correct answer, -20 per wrong answer or timeout, no healing, game over at 0 HP.
- Untimed reading; Ready starts a 10-second answer timer. Show an explanation after every answer, including the final mistake.
- Up to 18 fallacies, introduced progressively, with 2–8 answer choices.
- Team reviews educational content and supplies final art; coding can proceed with clearly identified draft content and placeholders.
- Async main loop, delta-time updates, project-relative asset paths, no blocking waits, and replaceable save storage prepare the code for a later browser build.

## M1 — One playable round

**Code:** `main.py`, `game.py`, `settings.py`, basic scene interface, `scenes/court.py`, reusable buttons and wrapped dialogue, `requirements.txt`, run instructions.

- Open the courtroom with placeholder Tomato, Chef, and gadget.
- Show one draft question and two static answer buttons.
- Ready → answer → correct/incorrect feedback and explanation.
- Lock the first answer so repeated clicks cannot resolve a round twice.
- Offer another round for testing.

**Done when:** The game opens and closes cleanly, both answer outcomes work, text fits, and launching from another working directory succeeds.

## M2 — A complete survival session

**Code:** session/round logic, `systems/question_bank.py`, starter `data/questions.json` and `data/fallacies.json`, HP bar, `scenes/results.py`.

- Load and validate editable JSON with helpful file/record errors.
- Start with the first two fallacy categories and enough draft questions to exercise the loop.
- Add score, HP, question number, correct/incorrect/timeout counts, and 10-second timeout.
- Centralize scoring and damage in one guarded resolution method.
- Shuffle eligible questions without changing source records; exhaust the bag before reshuffling and prevent consecutive repeats when multiple questions exist.
- Show final feedback before Game Over; Play Again resets the entire session.

**Done when:** Three correct answers give 300 points; each mistake costs exactly 20 HP; five mistakes end the run; rapid clicks and click/timeout boundaries produce one outcome; restart restores initial state.

## M3 — Full navigation and learning support

**Code:** title scene, six-step tutorial and separate practice round, guide overlay, pause menu, `systems/save_data.py`.

- Add Play, How to Play, best score, and desktop Quit.
- Tutorial practice changes no session score or HP.
- Formalize READING → ANSWERING → OBJECTION_ANIMATION → FEEDBACK; use a simple timed placeholder for the animation until M5.
- Add Guide and Pause with Resume, Restart, Return to Title.
- Freeze all gameplay updates under overlays and prevent click-through.
- Save high scores in the user's data folder; handle missing, corrupt, or unwritable saves safely.

**Done when:** Every screen is reachable, practice is isolated, pause/guide preserve the timer, and best score survives relaunch. A broken save does not crash the game.

## M4 — Progressive difficulty and all 18 fallacies

**Code:** difficulty system, `data/difficulty.json`, expanded question/guide data, dynamic answer generation and layout, unlock cards.

- Use the Section 5.7 order: Personal Attack, Bandwagon, False Dilemma, Appeal to Pity, Irrelevant Authority, Hasty Generalization, Straw Man, Red Herring, then the remaining categories.
- Start with two categories; unlock the third at question 6, then at 11, 16, 21, 26, 30, and every five questions afterward until all 18 are available.
- Answer count equals unlocked categories until eight, then stays capped at eight with the correct answer plus seven distinct unlocked distractors.
- Draw questions only from unlocked categories and rebuild the eligible bag at unlocks, preserving the immediate-repeat guard where possible.
- Show an untimed introduction card for each new fallacy; guide lists unlocked categories only.
- Support two/three-label lanes and a four-row, two-column layout for four to eight choices.
- Prepare at least two reviewed questions per category for release; treat the earlier 15 questions as additional drafts requiring review.

**Done when:** Boundary checks at questions 1, 6, 11, 16, 21, 26, 30, 35, and the final unlock produce the expected categories and choice counts. Locked fallacies never appear in questions or choices. Eight long labels remain readable without overlap.

## M5 — Motion, character reactions, art, and sound

**Code:** `entities/answer_target.py`, `entities/character.py`, `entities/projectile.py`, `systems/asset_loader.py`, asset documentation/credits.

- Steer labels through continuous smooth 2D curves throughout the shared padded answer box; randomize initial placement only, and support stationary labels through settings. The subsequent motion request expands the answer region and overrides the original straight-line bounce behavior. The latest request also removes all lane/cell movement restrictions and doubles nominal speed.
- Animate OBJECTION toward the gadget on correct answers; Chef reacts as judge.
- Select Tomato's expression from HP: normal 80–100, nervous 40–60, panic 0–20.
- Add a gentle, non-blocking red fade on wrong answers/timeouts.
- Integrate supplied Tomato art after checking its frames; load other team assets with labeled placeholders for missing art.
- Add sound loading, OGG/WAV fallback, mute button/M shortcut, and silent operation if audio fails.
- Bundle a licensed font and record asset credits.

**Done when:** Motion stays inside bounds without overlap, behaves consistently at different frame rates, and freezes under overlays. Faces match HP. Missing assets/audio do not crash. Animation cannot apply scoring twice.

## M6 — Release verification and handoff

**Code:** regression checks, content validation, bug fixes, complete README and manual checklist.

- Add focused automated checks alongside M2–M5 as their logic is built; consolidate them into one command here.
- Cover scoring, single resolution, timeout boundary, restart, question bags, unlock boundaries, choice validity, pause, saves, face thresholds, tint timing, and asset fallback.
- Run the source plan's manual checklist, updated for variable choices and eligible question pools.
- Check longest text, all screens, tutorial, and full eight-choice layout visually.
- Document installation, running, content editing, art replacement, settings, and known limitations.
- Fix issues found by team playtests; team approves educational content and final presentation.

**Done when:** Automated checks and manual checklist pass, no blocking bugs remain, and a non-coder can add a question and replace an image using the README. Record which operating systems were actually tested.

## M7 — Optional browser release

Depends on a stable desktop release.

- Package with pygbag and resolve browser-specific compatibility issues.
- Verify first-interaction audio, fonts, loading, browser-safe Quit behavior, and score storage/fallback.
- Test in Chrome and Firefox and document hosting/build steps.

**Done when:** A browser build supports the full title → game → results → replay flow, with responsive input, readable labels, and no blocking runtime errors. Publishing is a separate deployment action.

## Source conflicts resolved for this roadmap

1. **Three fixed choices versus 2–8:** Use the expanded scope and Section 5.7. Legacy three-choice examples/checklists must be updated.
2. **15 questions versus 36 plus 15 drafts:** Release requires coverage across all 18 categories; draft examples are not automatically approved content.
3. **Chef argues versus neutral judge:** Gadgets argue. Chef listens and rules; objection targets the gadget.
4. **Shuffle all questions versus progressive eligibility:** Exhaust the current eligible bag while its pool is unchanged; an unlock rebuilds the bag, so a global no-repeat guarantee across unlocks does not apply.
5. **Choices marked required but described as optional:** Generate playable choices from unlocked categories. If legacy explicit choices are supplied, validate their IDs, uniqueness, and inclusion of the answer; they must never force locked choices into play.
6. **Two-character layout versus three roles:** Reserve distinct space for Tomato, gadget, and Chef rather than copying the older two-character rectangles literally.

## Team work that can happen alongside coding

- Review definitions, question wording, explanations, and unlock order.
- Supply Tomato expressions, Chef/gadget reactions, courtroom background, and licensed font/sounds.
- Play each milestone and report reproducible bugs.
- Use placeholders and draft content to keep early coding moving; final release depends on content review and playtesting.

Next milestone: **M3**. Verify each milestone before building on it.
