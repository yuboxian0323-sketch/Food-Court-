"""Compare deterministic behavior and pixels with the pre-refactor local build.

Operation:
    Compare deterministic motion, progression, and unchanged pixels with saved
    baselines.
Input:
    Seeded scenarios, before_cleanup.json, and platform/Python/Pygame metadata.
Output:
    Assertions; runtime-specific exact checks skip on mismatched environments.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import random
import unittest

os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
import settings as s
from entities.answer_target import make_targets, update_targets
from game import Game
from scenes.court import Court
from systems.question_bank import QuestionBank
from systems.session import Session


def motion_fingerprints():
    """Hash every simulated/displayed state in seeded ten-second motion runs.

    Operation:
        Hash every simulated/displayed state in seeded ten-second motion runs.
    Input:
        Seeded two/eight-label simulations, 30/60/144 FPS, and movement settings.
    Output:
        Returns SHA-256 hashes of every motion/display state; only local simulation
        state changes.
    """
    bank = QuestionBank(s.ROOT / 'data')
    result = {}
    for count in (2, 8):
        for fps in (30, 60, 144):
            targets = make_targets(list(bank.fallacies)[:count], bank.fallacies, random.Random(42))
            digest = hashlib.sha256()
            for _ in range(10 * fps):
                update_targets(targets, 1 / fps)
                for target in targets:
                    values = (tuple(target.position), tuple(target.velocity),
                              tuple(target.draw_position), target.heading, target.turn_rate)
                    digest.update(repr(values).encode())
            result[f'{count}/{fps}'] = digest.hexdigest()
    return result


def progression_fingerprint():
    """Record question selection, choices, unlocks, and reactions through round 80.

    Operation:
        Record question selection, choices, unlocks, and reactions through round 80.
    Input:
        Seeded bank/session and the first 80 rounds.
    Output:
        Returns a SHA-256 hash of question/choice/unlock/reaction history.
    """
    session = Session(QuestionBank(s.ROOT / 'data', random.Random(2026)))
    rows = []
    for _ in range(80):
        session.acknowledge_unlock()
        session.ready()
        session.update(s.BOARD_ENTER_DURATION)
        session.answer(session.question.fallacy)
        rows.append((session.number, session.question.id, session.choices,
                     session.unlocked, session.score, session.hp,
                     session.gadget_expression, session.chef_expression,
                     session.tomato_expression))
        session.update(session.animation_remaining)
        session.continue_round()
        session.update(s.BOARD_EXIT_DURATION)
    return hashlib.sha256(repr(rows).encode()).hexdigest()


def image_fingerprints():
    """Capture unchanged court states, including red ribbons at all phases.

    Operation:
        Capture unchanged court states, including red ribbons at all phases.
    Input:
        Real court assets, a seeded session, and unchanged reading/mistake/transition
        states.
    Output:
        Returns frame hashes; creates/quits a temporary Pygame application.
    """
    game = Game()
    result = {}
    try:
        # Operation: Seed the actual scene after asset initialization; avoid hover
        #     variance.
        # Input: Loaded assets and fixed random seed.
        # Output: Reproducible bank/session/court for pixel comparisons.
        game.bank = QuestionBank(s.ROOT / 'data', random.Random(2026))
        game.session = Session(game.bank)
        game.scene = Court(game)
        session = game.session
        def capture(name):
            """Hash one actual court render without advancing simulation time.

            Operation:
                Hash one actual court render without advancing simulation time.
            Input:
                name: snapshot key; current rendered court/session.
            Output:
                Updates the local fingerprint mapping; returns None.
            """
            game.scene.draw(game.screen)
            result[name] = hashlib.sha256(pygame.image.tostring(game.screen, 'RGB')).hexdigest()
        capture('reading')
        session.ready()
        session.update(.17)
        capture('enter')
        session.update(s.BOARD_ENTER_DURATION)
        for _ in range(120):
            session.update(1 / 60)
        capture('answering')
        wrong = next(c for c in session.choices if c != session.question.fallacy)
        session.answer(wrong)
        for elapsed in (.1, .4, 1.0):
            session.animation_remaining = session.banner_duration - elapsed
            session.tint_remaining = max(0, s.MISTAKE_TINT_DURATION - elapsed)
            capture(f'wrong/{elapsed}')
        session.update(session.animation_remaining)
        capture('feedback')
        session.continue_round()
        session.update(.12)
        capture('exit')
        session.update(s.BOARD_EXIT_DURATION)
        session.ready()
        session.update(s.BOARD_ENTER_DURATION)
        session.update(s.ANSWER_TIME)
        session.update(.4)
        capture('timeout')
        return result
    finally:
        pygame.quit()


class PreservationTests(unittest.TestCase):
    """Protect numerical trajectories, content order, and unchanged presentation.

    Operation:
        Group regression checks against fixed seeded inputs and captured expectations.
    Input:
        unittest lifecycle and the current project code.
    Output:
        Assertions that report failures; no production behavior is changed.
    """

    @classmethod
    def setUpClass(cls):
        """Read immutable expectations captured from the starting worktree.

        Operation:
            Read immutable expectations captured from the starting worktree.
        Input:
            The checked-in pre-edit fixture JSON.
        Output:
            Sets the class fixture mapping; file/JSON errors propagate.
        """
        cls.expected = json.loads((Path(__file__).parent / 'fixtures/before_cleanup.json').read_text())

    def require_baseline_environment(self):
        """Skip exact hashes on platforms with different font or floating-point output.

        Operation:
            Skip exact hashes on platforms with different font or floating-point output.
        Input:
            Current platform/Python/Pygame and fixture runtime metadata.
        Output:
            Returns None or skips exact hashes on a different runtime.
        """
        current = dict(platform=sys.platform, python=platform.python_version(),
                       machine=platform.machine(), pygame=pygame.version.ver)
        if current != self.expected['environment']:
            self.skipTest('Exact numerical/pixel baseline belongs to a different runtime.')

    def test_motion_matches_baseline(self):
        """Steering, integration, interpolation, and speed must remain identical.

        Operation:
            Steering, integration, interpolation, and speed must remain identical.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        self.require_baseline_environment()
        self.assertEqual(motion_fingerprints(), self.expected['motion'])

    def test_progression_matches_baseline(self):
        """Refactoring must not consume random numbers or alter round outcomes.

        Operation:
            Refactoring must not consume random numbers or alter round outcomes.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        self.assertEqual(progression_fingerprint(), self.expected['progression'])

    def test_unchanged_scenes_match_baseline(self):
        """Require byte-identical pixels outside the requested green effect.

        Operation:
            Require byte-identical pixels outside the requested green effect.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        self.require_baseline_environment()
        self.assertEqual(image_fingerprints(), self.expected['images'])
