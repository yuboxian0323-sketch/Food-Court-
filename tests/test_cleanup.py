"""Compare banners and shared typography with the starting cleanup worktree.

Operation:
    Compare complete green/red ribbons, results, and button pixels against pre-edit
    captures.
Input:
    Seeded actual scenes and before_oio_cleanup.json from the starting worktree.
Output:
    Regression assertions and temporary Pygame state; exact hashes target the capture
    runtime.
"""
import hashlib
import json
import os
from pathlib import Path
import random
import unittest

os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
import settings as s
from game import Game
from scenes.court import Court
from scenes.results import Results
from systems.question_bank import QuestionBank
from systems.session import Session


def presentation_fingerprints():
    """Hash all banner phases, results, and enabled/disabled UI buttons.

    Operation:
        Render seeded scenarios and hash complete frames at fixed phase times.
    Input:
        Real assets, seeded outcomes, all ribbon phases, results, and button enabled
        states.
    Output:
        Returns banner/result/button hashes; creates/quits a temporary application.
    """
    game = Game()
    fingerprints = {}
    try:
        # Operation: Recreate the same seeded court for each supported outcome.
        # Input: Fixed RNG seed, source assets, and current rule constants.
        # Output: Resolved sessions ready for identical phase captures.
        for outcome in ('correct', 'incorrect', 'timeout'):
            game.bank = QuestionBank(s.ROOT / 'data', random.Random(10))
            game.session = Session(game.bank)
            game.scene = Court(game)
            session = game.session
            session.ready()
            session.update(s.BOARD_ENTER_DURATION)
            if outcome == 'timeout':
                session.update(s.ANSWER_TIME)
            else:
                selected = session.question.fallacy if outcome == 'correct' else next(
                    c for c in session.choices if c != session.question.fallacy)
                session.answer(selected)
            # Operation: Sample existing entrance, hold, and exit rendering.
            # Input: Resolved outcome and fixed elapsed times in seconds.
            # Output: SHA-256 frame hashes without changing the source fixtures.
            for elapsed in (.1, .4, 1.0, 1.1):
                session.animation_remaining = max(0, session.banner_duration - elapsed)
                session.tint_remaining = max(0, s.MISTAKE_TINT_DURATION - elapsed)
                game.scene.draw(game.screen)
                fingerprints[f'{outcome}/{elapsed}'] = hashlib.sha256(
                    pygame.image.tostring(game.screen, 'RGB')).hexdigest()
        # Operation: Exercise the centered-text call sites beyond the ribbon.
        # Input: Final session counters and enabled/disabled button states.
        # Output: Results/button hashes for exact before/after comparison.
        Results(game).draw(game.screen)
        fingerprints['results'] = hashlib.sha256(pygame.image.tostring(game.screen, 'RGB')).hexdigest()
        for enabled in (False, True):
            image = pygame.Surface((400, 150))
            image.fill('#392317')
            game.ui.button(image, (20, 20, 300, 56), 'Play Again', enabled)
            fingerprints[f'button/{enabled}'] = hashlib.sha256(
                pygame.image.tostring(image, 'RGB')).hexdigest()
        return fingerprints
    finally:
        pygame.quit()


class CleanupTests(unittest.TestCase):
    """Protect current green/red ribbons and the shared text-rendering call sites.

    Operation:
        Group regression checks against fixed seeded inputs and captured expectations.
    Input:
        unittest lifecycle and the current project code.
    Output:
        Assertions that report failures; no production behavior is changed.
    """

    def test_presentations_match_before_cleanup(self):
        """Require exactly the pixels captured before this documentation pass.

        Operation:
            Require exactly the pixels captured before this documentation pass.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        path = Path(__file__).parent / 'fixtures/before_oio_cleanup.json'
        expected = json.loads(path.read_text())
        self.assertEqual(presentation_fingerprints(), expected)
