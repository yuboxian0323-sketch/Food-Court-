from helpers import begin_answering, finish_result, ready_frame
import copy
import os
import random
import unittest
from unittest.mock import patch

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import pygame
import settings as s
from entities.answer_target import make_targets, update_targets
from systems.question_bank import QuestionBank
from systems.session import Session
from systems.tomato import Tomato
from game import Game
from scenes.court import Court
from scenes.results import Results


class GameplayRulesTests(unittest.TestCase):
    def setUp(self):
        self.bank = QuestionBank(s.ROOT / 'data', random.Random(17))
        self.session = Session(self.bank)

    def test_all_unlocks_and_generated_answers(self):
        expected = {1:2, 6:3, 11:4, 16:5, 21:6, 26:7, 30:8,
                    **{q:8+(q-30)//5 for q in range(35,81,5)}}
        for number in range(1,101):
            session = self.session
            available = expected[max(q for q in expected if q<=number)]
            self.assertEqual(session.number, number)
            self.assertEqual(len(session.unlocked), available)
            self.assertEqual(len(session.choices), min(8, available))
            self.assertEqual(len(set(session.choices)),len(session.choices))
            self.assertEqual(session.choices.count(session.question.fallacy),1)
            self.assertTrue(set(session.choices)<=set(session.unlocked))
            self.assertIn(session.question.fallacy,session.unlocked)
            if number in expected and number > 1:
                self.assertTrue(session.new_fallacies)
                begin_answering(session)
                self.assertEqual(session.stage,'READING')
            session.acknowledge_unlock()
            begin_answering(session)
            session.answer(session.question.fallacy)
            self.assertEqual(session.stage,'OBJECTION_ANIMATION')
            self.assertEqual(session.animation_remaining,s.OBJECTION_DURATION)
            self.assertEqual(session.tint_alpha,0)
            self.assertFalse(session.answer(session.question.fallacy))
            session.update(s.OBJECTION_DURATION)
            self.assertEqual(session.stage,'FEEDBACK')
            session.next_round()
        self.assertEqual(self.session.score,10000)
        self.assertEqual(self.session.hp,100)

    def test_eligible_bags_and_rebuilds_without_mutation(self):
        original=copy.deepcopy(self.bank.questions)
        self.bank.reset()
        last=None
        for available in [tuple(self.bank.fallacies)[:2],tuple(self.bank.fallacies)[:3],tuple(self.bank.fallacies)]:
            eligible=[q for q in original if q.fallacy in available]
            for _ in range(3):
                ids=[]
                for _ in eligible:
                    q=self.bank.draw(available)
                    self.assertNotEqual(q.id,last)
                    self.assertIn(q.fallacy,available)
                    last=q.id
                    ids.append(q.id)
                self.assertEqual(len(set(ids)),len(eligible))
        self.assertEqual(self.bank.questions,original)

    def test_wrong_timeout_tint_and_expression_bands(self):
        for i,outcome in enumerate(['incorrect','timeout','incorrect','timeout','incorrect']):
            session=self.session
            begin_answering(session)
            if outcome=='timeout':
                session.update(s.ANSWER_TIME)
            else:
                session.answer(next(c for c in session.choices if c!=session.question.fallacy))
            self.assertEqual(session.stage,'MISTAKE_ANIMATION')
            self.assertEqual(session.animation_remaining,session.banner_duration)
            self.assertEqual(session.hp,80-20*i)
            self.assertEqual(session.tint_alpha,80)
            self.assertEqual(session.gadget_expression,'smug')
            self.assertEqual(session.chef_expression,'stern')
            self.assertEqual(session.tomato_expression,['normal','nervous','nervous','panic','panic'][i])
            self.assertFalse(session.resolve_round('timeout'))
            session.update(.25)
            self.assertEqual(session.tint_alpha,40)
            session.update(.25)
            self.assertEqual(session.tint_alpha,0)
            finish_result(session)
            session.next_round()
        self.assertTrue(session.game_over)
        self.assertEqual(session.counts,dict(correct=0,incorrect=3,timeout=2))

    def test_settings_expression_thresholds_and_restart_at_late_progression(self):
        session=self.session
        with patch.object(s,'FACE_NORMAL_MIN_HP',90),patch.object(s,'FACE_NERVOUS_MIN_HP',50):
            for hp,expected in [(100,'normal'),(80,'nervous'),(40,'panic'),(0,'panic')]:
                session.hp=hp
                self.assertEqual(session.expression_for_hp(),expected)
        session.hp=100
        session.number=79
        session.next_round()
        self.assertEqual(len(session.unlocked),18)
        session.acknowledge_unlock()
        begin_answering(session)
        session.answer(next(c for c in session.choices if c!=session.question.fallacy))
        session.restart()
        self.assertEqual((session.number,session.hp,session.score),(1,100,0))
        self.assertEqual(len(session.unlocked),2)
        self.assertEqual(len(session.targets),2)
        self.assertEqual(session.stage,'READING')
        self.assertFalse(session.new_fallacies)
        self.assertFalse(session.resolved)
        self.assertIsNone(session.selected)
        self.assertEqual(session.tint_alpha,0)
        self.assertEqual(session.animation_remaining,0)
        self.assertEqual(session.tomato_expression,'normal')
        self.assertEqual(session.gadget_expression,'talking')
        self.assertEqual(session.chef_expression,'listening')
        self.assertEqual(session.remaining,10)
        self.assertTrue(all(value==0 for value in session.counts.values()))


class TargetsTests(unittest.TestCase):
    def setUp(self):
        self.bank=QuestionBank(s.ROOT/'data',random.Random(1))

    def test_bounds_non_overlap_long_frames_and_speed(self):
        for count in range(2,9):
            targets=make_targets(list(self.bank.fallacies)[:count],self.bank.fallacies,random.Random(2))
            for dt in [0,1/60,1/30,.5,10,10000]:
                update_targets(targets,dt)
                for t in targets:
                    self.assertTrue(pygame.Rect(s.LABEL_REGION).contains(t.rect))
                    self.assertTrue(pygame.Rect(t.bounds).contains(t.rect))
                for i,t in enumerate(targets):
                    self.assertFalse(any(t.rect.colliderect(other.rect) for other in targets[i+1:]))
            a=copy.deepcopy(targets[0]);b=copy.deepcopy(a)
            for _ in range(300): a.update(1/30)
            for _ in range(1440): b.update(1/144)
            self.assertAlmostEqual(a.x,b.x,places=6)
            with patch.object(s,'LABEL_SPEED_MULTIPLIER',0):
                x=a.x;a.update(100)
                self.assertEqual(a.x,x)

    def test_hit_position_moves_with_target(self):
        t=make_targets(list(self.bank.fallacies)[:2],self.bank.fallacies,random.Random(5))[0]
        old=t.rect.copy()
        for _ in range(120):t.update(1/60)
        self.assertNotEqual(old.topleft,t.rect.topleft)
        self.assertTrue(t.contains(t.rect.center))
        self.assertFalse(t.contains((t.rect.right+1,t.rect.centery)))

    def test_correct_answer_position_varies(self):
        slots=set()
        session=Session(self.bank)
        for _ in range(30):
            t=next(t for t in session.targets if t.fallacy_id==session.question.fallacy)
            slots.add(tuple(t.position))
            session.next_round()
        self.assertGreater(len(slots),1)


class RenderingAndInputTests(unittest.TestCase):
    def setUp(self): self.game=Game()
    def tearDown(self): pygame.quit()

    def click(self,rect):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pygame.Rect(rect).center)

    def test_click_after_movement_and_correct_animation_cannot_skip(self):
        game=self.game;session=game.session
        ready_frame(game,self.click(s.ACTION))
        game.frame([],2)
        target=next(t for t in session.targets if t.fallacy_id==session.question.fallacy)
        pos=target.rect.center
        session.remaining=.001
        game.frame([self.click(target.rect)]*5,.1)
        self.assertEqual(session.score,100)
        self.assertEqual(session.hp,100)
        self.assertEqual(session.stage,'OBJECTION_ANIMATION')
        game.frame([self.click(s.ACTION)]*5,.5)
        self.assertEqual(session.stage,'OBJECTION_ANIMATION')
        game.frame([], .7)
        self.assertEqual(session.stage,'FEEDBACK')
        self.assertEqual(session.score,100)
        game.frame([self.click(s.ACTION)]*5,0)
        game.frame([],s.BOARD_EXIT_DURATION)
        self.assertEqual(session.stage,'READING')
        self.assertEqual(session.number,2)

    def test_feedback_and_reading_targets_are_frozen_tint_does_not_block(self):
        game=self.game;session=game.session
        positions=[t.x for t in session.targets]
        game.frame([],100)
        self.assertEqual(positions,[t.x for t in session.targets])
        ready_frame(game,self.click(s.ACTION))
        game.frame([],10)
        self.assertEqual(session.tint_alpha,80)
        positions=[t.x for t in session.targets]
        game.frame([], .1)
        self.assertEqual(positions,[t.x for t in session.targets])
        game.frame([],session.animation_remaining)
        game.frame([self.click(s.ACTION)],0)
        game.frame([],s.BOARD_EXIT_DURATION)
        self.assertEqual(session.stage,'READING')
        self.assertEqual(session.tint_alpha,0)

    def test_all_text_and_label_counts_fit(self):
        game=self.game;ui=game.ui
        for q in game.bank.questions:
            for text in (q.argument,q.explanation):
                lines=ui.wrap(text,968,28)
                self.assertLessEqual(len(lines)*ui.fonts[28].get_linesize(),64,q.id)
        for metadata in game.bank.fallacies.values():
            text=metadata['definition']+'\nExample: '+metadata['example']
            self.assertLessEqual(len(ui.wrap(text,968,24))*ui.fonts[24].get_linesize(),72,metadata['id'])
        for count in range(2,9):
            # Put every name in every size, including late-game names in lanes.
            for name in game.bank.fallacies:
                choices=[name]+[id_ for id_ in game.bank.fallacies if id_!=name][:count-1]
                targets=make_targets(choices,game.bank.fallacies,random.Random(5))
                size=20 if count>3 else 24
                for target in targets:
                    lines=ui.wrap(target.name,target.width-16,size)
                    self.assertTrue(all(ui.fonts[size].size(line)[0]<=target.width-16 for line in lines))
                    self.assertLessEqual((len(lines)+1)*ui.fonts[size].get_linesize(),target.height)
                game.session.targets=targets
                game.session.stage='FEEDBACK'
                game.session.result='correct'
                for target in targets:target.feedback='correct'
                game.scene.draw(game.screen)

    def test_missing_tomato_image_falls_back(self):
        with patch('pygame.image.load',side_effect=FileNotFoundError('missing image')):
            tomato=Tomato()
        self.assertFalse(tomato.frames)
        for hp in (100,60,20,0):tomato.draw(self.game.screen,hp)
        self.game.frame([],0)

    def test_all_round_stages_close_cleanly(self):
        for stage in ('READING','ANSWERING','OBJECTION_ANIMATION','FEEDBACK'):
            self.game.running=True
            self.game.session.stage=stage
            self.game.session.animation_remaining=1.2
            if stage=='FEEDBACK': self.game.session.result='timeout'
            self.game.frame([pygame.event.Event(pygame.QUIT)],0)
            self.assertFalse(self.game.running)


if __name__=='__main__':unittest.main()
