from helpers import begin_answering, finish_result, ready_frame
import copy
import json
import os
import random
import tempfile
import unittest
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import pygame
import settings
from systems.question_bank import QuestionBank, ContentError
from systems.session import Session
from game import Game, ErrorScene
from scenes.court import Court
from scenes.results import Results


class RulesTests(unittest.TestCase):
    def setUp(self):
        self.bank = QuestionBank(settings.ROOT / 'data', random.Random(7))
        self.session = Session(self.bank)

    def resolve(self, correct=True):
        begin_answering(self.session)
        answer = self.session.question.fallacy
        if not correct:
            answer = next(c for c in self.session.choices if c != answer)
        self.session.answer(answer)

    def test_scoring_and_exactly_once(self):
        for _ in range(3):
            self.resolve()
            self.assertFalse(self.session.resolve_round('incorrect'))
            self.session.update(100)
            self.session.next_round()
        self.assertEqual((self.session.score, self.session.hp), (300, 100))
        self.resolve(False)
        self.assertEqual(self.session.hp, 80)
        self.assertEqual(self.session.counts, dict(correct=3, incorrect=1, timeout=0))

    def test_timer_reading_game_over_restart(self):
        self.session.update(100)
        self.assertEqual(self.session.remaining, settings.ANSWER_TIME)
        self.assertFalse(self.session.answer(self.session.question.fallacy))
        for _ in range(5):
            begin_answering(self.session)
            self.session.update(settings.ANSWER_TIME)
            self.session.update(50)
            self.assertEqual(self.session.stage, 'FEEDBACK')
            self.session.next_round()
        self.assertEqual(self.session.hp, 0)
        self.assertTrue(self.session.game_over)
        self.assertEqual(self.session.counts['timeout'], 5)
        self.assertFalse(self.session.answer(self.session.question.fallacy))
        self.session.restart()
        self.assertEqual((self.session.hp, self.session.score, self.session.number), (100, 0, 1))
        self.assertEqual(self.session.stage, 'READING')
        self.assertEqual(self.session.remaining, settings.ANSWER_TIME)
        self.assertFalse(self.session.resolved)
        self.assertTrue(all(n == 0 for n in self.session.counts.values()))

    def test_shuffle_bag_and_no_mutation(self):
        self.bank.reset()
        original = copy.deepcopy(self.bank.questions)
        previous = None
        for _ in range(10):
            batch = []
            for _ in self.bank.questions:
                q = self.bank.draw()
                self.assertNotEqual(previous, q.id)
                batch.append(q.id)
                previous = q.id
            self.assertEqual(len(set(batch)), len(self.bank.questions))
        self.assertEqual(self.bank.questions, original)

    def test_content_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('fallacies', 'questions'):
                (root / f'{name}.json').write_text((settings.ROOT / 'data' / f'{name}.json').read_text())
            original = json.loads((root / 'questions.json').read_text())
            for mutation in ('duplicate', 'unknown', 'long', 'choices', 'not_object'):
                content = copy.deepcopy(original)
                row = content['questions'][0]
                if mutation == 'duplicate':
                    row['id'] = content['questions'][1]['id']
                elif mutation == 'unknown':
                    row['fallacy'] = 'missing'
                elif mutation == 'long':
                    row['argument'] = 'x' * 221
                elif mutation == 'choices':
                    row['choices'] = ['ad_hominem', 'ad_hominem']
                else:
                    content['questions'][0] = []
                (root / 'questions.json').write_text(json.dumps(content))
                with self.assertRaisesRegex(ContentError, 'questions.json'):
                    QuestionBank(root)
            (root / 'questions.json').write_text('{broken')
            with self.assertRaisesRegex(ContentError, 'questions.json'):
                QuestionBank(root)


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def tearDown(self):
        pygame.quit()

    def click(self, rect):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pygame.Rect(rect).center)

    def test_boundary_input_and_queued_clicks(self):
        game = self.game
        session = game.session
        ready_frame(game,self.click(Court.action))
        session.remaining = .001
        index = session.choices.index(session.question.fallacy)
        game.frame([self.click(session.targets[index].rect)] * 8, .1)
        self.assertEqual((session.score, session.hp), (100, 100))
        self.assertEqual(session.counts['timeout'], 0)
        game.frame([],settings.OBJECTION_DURATION)
        game.frame([self.click(Court.action)] * 8, 0)
        game.frame([],settings.BOARD_EXIT_DURATION)
        self.assertEqual(session.number, 2)
        self.assertEqual(session.stage, 'READING')

    def test_full_session_results_restart_and_close(self):
        game = self.game
        for _ in range(5):
            ready_frame(game,self.click(Court.action))
            game.frame([], settings.ANSWER_TIME)
            game.frame([],game.session.banner_duration)
            self.assertEqual(game.session.stage, 'FEEDBACK')
            game.frame([self.click(Court.action)],0)
            game.frame([],settings.BOARD_EXIT_DURATION)
        self.assertIsInstance(game.scene, Results)
        game.frame([self.click(Results.again)] * 3, 0)
        self.assertIsInstance(game.scene, Court)
        self.assertEqual(game.session.hp, 100)
        self.assertEqual(game.session.stage, 'READING')
        game.frame([pygame.event.Event(pygame.QUIT)], 0)
        self.assertFalse(game.running)

    def test_text_fits_and_sprite_loaded(self):
        ui = self.game.ui
        self.assertEqual(len(self.game.tomato.frames), 5)
        for q in self.game.bank.questions:
            for text, width, height in ((q.argument, 968, 80), (q.explanation, 968, 80)):
                lines = ui.wrap(text, width)
                self.assertLessEqual(len(lines)*ui.fonts[28].get_linesize(), height)
                self.assertTrue(all(ui.fonts[28].size(line)[0] <= width for line in lines))
        self.game.scene = ErrorScene(self.game, 'questions.json: q001: invalid fallacy')
        self.game.frame([], 0)


if __name__ == '__main__':
    unittest.main()
