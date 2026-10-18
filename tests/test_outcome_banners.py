"""Protect shared ribbon timing, colors, input guards, and unchanged reactions.

Operation:
    Drive actual scenes through outcome, timing, input, and reset regression checks.
Input:
    Fresh seeded games, mocked render calls, synthetic events, and existing rule
    constants.
Output:
    Assertions and disposable application state; no production asset/content writes.
"""
import os
import random
import unittest
from unittest.mock import patch

os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
import settings as s
from game import Game
from scenes.court import Court
from systems.question_bank import QuestionBank
from systems.session import Session


class OutcomeBannerTests(unittest.TestCase):
    """Drive real scenes through the three outcomes without introducing new rules.

    Operation:
        Group regression checks against fixed seeded inputs and captured expectations.
    Input:
        unittest lifecycle and the current project code.
    Output:
        Assertions that report failures; no production behavior is changed.
    """

    def setUp(self):
        """Create a reproducible application with the board fully entered.

        Operation:
            Create a reproducible application with the board fully entered.
        Input:
            A fresh application and reproducible session.
        Output:
            Creates game/session/scene references; returns None.
        """
        self.game = Game()
        self.game.bank = QuestionBank(s.ROOT / 'data', random.Random(10))
        self.game.session = Session(self.game.bank)
        self.game.scene = Court(self.game)
        self.session = self.game.session
        self.session.ready()
        self.session.update(s.BOARD_ENTER_DURATION)

    def tearDown(self):
        """Release display/font resources between application tests.

        Operation:
            Release display/font resources between application tests.
        Input:
            Temporary test/application state.
        Output:
            Quits Pygame resources; returns None.
        """
        pygame.quit()

    def resolve(self, outcome):
        """Trigger an outcome using its normal click or timer route.

        Operation:
            Trigger an outcome using its normal click or timer route.
        Input:
            outcome: correct/incorrect/timeout; the current answering session.
        Output:
            Resolves the current session by answer or timeout; returns None.
        """
        if outcome == 'timeout':
            self.session.update(s.ANSWER_TIME)
        else:
            choice = self.session.question.fallacy if outcome == 'correct' else next(
                c for c in self.session.choices if c != self.session.question.fallacy)
            self.session.answer(choice)

    def test_shared_geometry_shadow_and_lettering(self):
        """Color configuration must preserve every ribbon's shape and white text.

        Operation:
            Color configuration must preserve every ribbon's shape and white text.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        court = self.game.scene
        red = court.banner('OBJECTION!')
        green = court.banner('OBJECTION!', '#28784b')
        self.assertEqual(red.get_size(), green.get_size())
        self.assertEqual(pygame.mask.from_surface(red).to_surface().get_buffer().raw,
                         pygame.mask.from_surface(green).to_surface().get_buffer().raw)
        for image, expected in ((red, '#bd4034'), (green, '#28784b')):
            self.assertEqual(image.get_at((40, 50)), pygame.Color(expected))
        white = (255, 246, 229, 255)
        red_text = pygame.mask.from_threshold(red, white, (1, 1, 1, 1))
        green_text = pygame.mask.from_threshold(green, white, (1, 1, 1, 1))
        self.assertGreater(red_text.count(), 100)
        self.assertEqual(red_text.overlap_area(green_text, (0, 0)), red_text.count())

    def test_colors_follow_identical_entrance_hold_exit_positions(self):
        """Shared phase equations must place both colors at the same screen pixels.

        Operation:
            Shared phase equations must place both colors at the same screen pixels.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        court = self.game.scene
        for elapsed in (0, .1, .2, .4, .85, 1.0, 1.1):
            self.session.animation_remaining = self.session.banner_duration - elapsed
            surfaces = []
            for color in ('#bd4034', '#28784b'):
                image = pygame.Surface((s.WIDTH, s.HEIGHT), pygame.SRCALPHA)
                court.draw_outcome_banner(image, 'OBJECTION!', color)
                surfaces.append(pygame.mask.from_surface(image).to_surface())
            self.assertEqual(pygame.image.tostring(surfaces[0], 'RGB'),
                             pygame.image.tostring(surfaces[1], 'RGB'))

    def test_correct_uses_only_green_shared_renderer(self):
        """Correct answers route to the green ribbon, never the red wrapper.

        Operation:
            Correct answers route to the green ribbon, never the red wrapper.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        self.resolve('correct')
        with patch.object(self.game.scene, 'draw_outcome_banner') as shared:
            self.game.scene.draw(self.game.screen)
        shared.assert_called_once_with(self.game.screen, 'OBJECTION!', '#28784b')

    def test_wrong_and_timeout_remain_red(self):
        """Each mistake keeps its configured message and the default red palette.

        Operation:
            Each mistake keeps its configured message and the default red palette.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        for outcome, message in (('incorrect', s.WRONG_BANNER_TEXT),
                                 ('timeout', s.TIMEOUT_BANNER_TEXT)):
            self.session.restart()
            self.session.ready()
            self.session.update(s.BOARD_ENTER_DURATION)
            self.resolve(outcome)
            with patch.object(self.game.scene, 'draw_outcome_banner') as shared:
                self.game.scene.draw(self.game.screen)
            shared.assert_called_once_with(self.game.screen, message)

    def test_all_outcomes_finish_before_feedback_and_cannot_repeat(self):
        """One resolution freezes choices, applies rules once, and gates Continue.

        Operation:
            One resolution freezes choices, applies rules once, and gates Continue.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        for outcome in ('correct', 'incorrect', 'timeout'):
            self.session.restart()
            self.session.ready()
            self.session.update(s.BOARD_ENTER_DURATION)
            self.resolve(outcome)
            state = self.session.stage
            positions = [tuple(t.position) for t in self.session.targets]
            self.assertEqual(self.session.animation_remaining, self.session.banner_duration)
            self.assertEqual(self.session.score, 100 if outcome == 'correct' else 0)
            self.assertEqual(self.session.hp, 100 if outcome == 'correct' else 80)
            self.assertEqual(self.session.gadget_expression,
                             'shocked' if outcome == 'correct' else 'smug')
            self.assertEqual(self.session.chef_expression,
                             'surprised' if outcome == 'correct' else 'stern')
            for _ in range(4):
                self.assertFalse(self.session.answer(self.session.question.fallacy))
                self.assertFalse(self.session.resolve_round(outcome))
                self.session.continue_round()
            self.assertEqual(self.session.stage, state)
            self.session.update(self.session.banner_duration - .001)
            self.assertEqual(self.session.stage, state)
            self.assertEqual(positions, [tuple(t.position) for t in self.session.targets])
            self.session.update(.001)
            self.assertEqual(self.session.stage, 'FEEDBACK')
            self.assertEqual(sum(self.session.counts.values()), 1)

    def test_input_batch_does_not_skip_banner_or_feedback(self):
        """Repeated queued clicks cannot resolve twice or continue during a ribbon.

        Operation:
            Repeated queued clicks cannot resolve twice or continue during a ribbon.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        target = next(t for t in self.session.targets if t.fallacy_id == self.session.question.fallacy)
        answer = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=target.rect.center)
        action = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pygame.Rect(s.ACTION).center)
        self.game.frame([answer] * 3 + [action] * 3, 5)
        self.assertEqual(self.session.stage, 'OBJECTION_ANIMATION')
        self.assertEqual(self.session.score, 100)
        self.game.frame([action] * 3, .1)
        self.assertEqual(self.session.stage, 'OBJECTION_ANIMATION')
        self.game.frame([], self.session.animation_remaining)
        self.assertEqual(self.session.stage, 'FEEDBACK')

    def test_zero_time_updates_freeze_banner_and_motion(self):
        """A frozen update retains animation time and target positions exactly.

        Operation:
            A frozen update retains animation time and target positions exactly.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        self.resolve('correct')
        before = self.session.animation_remaining
        positions = [tuple(t.position) for t in self.session.targets]
        self.session.update(0)
        self.assertEqual(before, self.session.animation_remaining)
        self.assertEqual(positions, [tuple(t.position) for t in self.session.targets])

    def test_restart_clears_animation_and_outcomes(self):
        """Restart discards the banner, previous feedback, and all session totals.

        Operation:
            Restart discards the banner, previous feedback, and all session totals.
        Input:
            Fixture expectations and a fresh or seeded session/application.
        Output:
            Assertions succeed or raise a unittest failure; temporary surfaces/session
            state may be changed.
        """
        self.resolve('incorrect')
        self.game.restart()
        self.assertEqual(self.session.stage, 'READING')
        self.assertEqual(self.session.animation_remaining, 0)
        self.assertEqual(self.session.transition_remaining, 0)
        self.assertEqual(self.session.tint_remaining, 0)
        self.assertEqual((self.session.hp, self.session.score), (100, 0))
        self.assertIsNone(self.session.result)
        self.assertEqual(sum(self.session.counts.values()), 0)
