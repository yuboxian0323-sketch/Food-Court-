# Outcome ribbon and documentation cleanup

Work is local to `codex/gameplay-updates`; `Ver3` was not changed. The existing local Chef asset-path correction is retained.

## Requested presentation change

The correct-only `OBJECTION!` effect now uses the existing ribbon geometry, white typography, shadow, screen placement, and entrance/hold/exit equations. Its background is rich green (`#28784b`). Incorrect and timeout ribbons retain their original red palette and configurable messages. All ribbons run for 0.20 + 0.65 + 0.25 = 1.10 seconds; the public `OBJECTION_DURATION` setting now reflects this duration. The old traveling gold effect was replaced, not layered underneath.

The session continues to own exactly-once scoring/damage and stage changes. Existing correct/mistake stage names and character reactions remain. Feedback and Continue appear after the ribbon exits.

## Consolidation and documentation

- `scenes/court.py`: one cached ribbon builder and one phase renderer, parameterized by message and background. Existing drawing entry points and default red cache keys are retained.
- `systems/expressions.py`, `systems/session.py`, `systems/tomato.py`, and `systems/scene_assets.py`: shared Tomato HP thresholds and normal/nervous/panic frame mapping. The existing mistake-only red Tomato frame and decaying shake are preserved.
- `ui/widgets.py`, `scenes/court.py`, and `scenes/results.py`: shared centered-text rendering with the same font calls and rectangle placement.
- All project-owned Python modules, classes, and functions now have documentation. Longer steering, separation, asset extraction, compositing, event, reset, and state-transition blocks have intent and invariant comments. The duplicate Pygame import in `entities/chef.py` was removed.
- Additional documentation-only files: `entities/answer_target.py`, `entities/character.py`, `entities/chef.py`, `game.py`, `main.py`, `scenes/base.py`, `systems/difficulty.py`, `systems/question_bank.py`, and `ui/target_renderer.py`. `settings.py` documents configuration units and the compatible correct-effect duration. README describes the new ribbon.
- `tests/test_outcome_banners.py`, `tests/test_preservation.py`, and `tests/fixtures/before_cleanup.json` provide new regression coverage. `output/green-objection-banner.png` is an actual rendered hold frame.

## Verification

Before editing, the 43 tests recovered from the saved Ver 2 backup all passed against the current Ver3-based worktree. The saved suite was run externally from `/private/tmp`; its expectations were not edited. All 43 pass after the cleanup as well.

Eleven new tests cover ribbon color, shape, white lettering, shared phase positions, one renderer per outcome, exactly-once resolution, reactions, frozen labels, blocked queued clicks, feedback timing, and restart. Preservation fixtures were captured before source edits. They compare full ten-second motion traces with two/eight labels at 30/60/144 FPS, seeded question/choice/unlock progression through round 80, and exact pixels for reading, board entrance, answering, wrong-banner entrance/hold/exit, feedback, board exit, and timeout. All comparisons passed on the local runtime. Exact floating-point and pixel hashes are runtime-specific and skip on a different platform/Python/Pygame combination; portable rule/banner tests remain active.

Executable syntax trees, with docstrings excluded, are identical for movement, content selection, difficulty, target rendering, fallback character drawing, the base scene, and the launcher. No source art, JSON content, or movement settings were changed. Python compilation and `git diff --check` pass.

Actual game-loop frames were captured and visually inspected for green/red ribbon entrance, hold, exit, and subsequent explanations. These are rendered-frame checks; native mouse interaction, display-compositor smoothness, and a human playtest were not verified by these captures.

## Deliberately retained behavior and limitations

There is no existing pause control. Zero-delta updates freeze the banner and target state; no pause feature was added.

The two Tomato loaders use different crops/scales and fallback drawings. They were retained because merging them could change pixels. Legacy public Chef/gadget renderers, `game.chef`, `game.tomato`, and `Session.objection_progress` remain for interface compatibility. The court still uses its existing drawn Chef portrait. The unused legacy Chef player's `update()` expects a `frame_duration` attribute not initialized by its constructor; this pre-existing issue was not changed or activated.

The work intentionally does not add menus, alter the layout, replace assets, change steering calculations, or modify progression. Verification supports preservation for the tested inputs and rendered states, not an exhaustive claim about every possible runtime or input sequence.

Run the new checks from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

## Operation / Input / Output follow-up

The subsequent cleanup keeps the already-green ribbon unchanged. Every project-owned Python module, class, function, and meaningful existing block comment now uses the exact `Operation:`, `Input:`, and `Output:` labels. Contracts identify direct arguments and relevant state, scene-pixel coordinates, seconds, returned values, mutated state, rendered output, and important error/fallback behavior. Coherent phases within steering, rectangle avoidance, integration, asset extraction, scene layering, event handling, outcome application, and resets are documented separately; obvious legacy comments duplicated by short function contracts were removed. Third-party, virtual-environment, and generated files were excluded.

Additional executable changes are limited to three rendering modules:

- `ui/widgets.py`: the legacy button now delegates label placement to `UI.centered_text`.
- `scenes/court.py`: cached banner lettering delegates to the same centered-text implementation; hidden-target prewarming uses the shared label-font selector.
- `ui/target_renderer.py`: `label_font_size(count)` supplies the unchanged 20/24 size choice to both prewarming and active label rendering.

The existing shared outcome renderer, HP-expression selection, resolution guard, transitions, and resets were reviewed and retained. The new pass changes no gameplay numerical operations, timing settings, random calls, event order, asset loading, or saved-data formats. A current-worktree source snapshot confirms identical executable syntax trees outside the three listed rendering modules, including tests after excluding docstrings.

Before editing, all 11 current tests and 43 externally recovered gameplay tests passed. After editing, all 12 current tests and the same unmodified 43 gameplay tests pass (55 total). The new `tests/test_cleanup.py` and `tests/fixtures/before_oio_cleanup.json` compare exact pre-edit green/red banner phase pixels, results-screen pixels, and enabled/disabled button pixels. These additional pixel hashes target the capture machine/runtime. Existing seeded motion/progression and unchanged-scene comparisons also pass. No test expectations were changed to accept an unintended result. Documentation coverage and syntax-tree audits pass, as does `git diff --check`.

New actual-game frames were visually inspected across green/red entrance, hold, exit, and explanations. Physical monitor smoothness and native manual interaction were not inspected. Legacy loader crop/fallback differences, the existing lack of a pause control, and the unused Chef player's uninitialized `frame_duration` issue remain deliberately unchanged. Prior unrelated local edits, including the startup asset-path fix, are retained; `Ver3` was not modified.
