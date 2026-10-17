import os
import random
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ['SDL_VIDEODRIVER']='dummy'
import pygame
import settings as s
from game import Game
from systems.question_bank import QuestionBank
from systems.session import Session
from systems.scene_assets import SceneAssets
from helpers import begin_answering


class BoardStateTests(unittest.TestCase):
    def setUp(self):
        self.session=Session(QuestionBank(s.ROOT/'data',random.Random(8)))

    def test_entrance_is_untimed_and_not_clickable_then_full_ten_seconds(self):
        t=self.session
        original=[x.position.copy() for x in t.targets]
        t.update(100)
        self.assertEqual(t.remaining,10)
        t.ready()
        self.assertEqual(t.stage,'BOARD_ENTER')
        self.assertFalse(t.answer(t.question.fallacy))
        t.continue_round()
        t.update(s.BOARD_ENTER_DURATION/2)
        self.assertEqual(t.stage,'BOARD_ENTER')
        self.assertEqual(t.remaining,10)
        self.assertEqual(original,[x.position for x in t.targets])
        t.update(10)  # A long transition frame cannot eat answering time.
        self.assertEqual(t.stage,'ANSWERING')
        self.assertEqual(t.remaining,10)
        t.update(.1)
        self.assertAlmostEqual(t.remaining,9.9)

    def test_wrong_banner_once_and_continue_only_after_explanation(self):
        t=self.session;begin_answering(t)
        wrong=next(c for c in t.choices if c!=t.question.fallacy)
        self.assertTrue(t.answer(wrong))
        self.assertEqual(t.stage,'MISTAKE_ANIMATION')
        self.assertEqual(t.hp,80)
        positions=[x.position.copy() for x in t.targets]
        for _ in range(10):
            self.assertFalse(t.resolve_round('incorrect',wrong))
            self.assertFalse(t.answer(t.question.fallacy))
            t.continue_round()
        self.assertEqual(t.stage,'MISTAKE_ANIMATION')
        t.update(t.banner_duration-.01)
        self.assertEqual(t.stage,'MISTAKE_ANIMATION')
        self.assertEqual(positions,[x.position for x in t.targets])
        t.update(.01)
        self.assertEqual(t.stage,'FEEDBACK')
        self.assertEqual(t.counts,dict(correct=0,incorrect=1,timeout=0))
        self.assertEqual(t.score,0)

    def test_timeout_uses_mistake_banner_and_never_awards_points(self):
        t=self.session;begin_answering(t)
        t.update(10)
        self.assertEqual(t.stage,'MISTAKE_ANIMATION')
        self.assertEqual(t.result,'timeout')
        self.assertEqual(t.hp,80)
        self.assertFalse(t.answer(t.question.fallacy))
        t.update(t.banner_duration)
        self.assertEqual(t.stage,'FEEDBACK')
        self.assertEqual(t.score,0)
        self.assertEqual(t.counts['timeout'],1)

    def test_correct_animation_is_distinct_and_cannot_be_skipped(self):
        t=self.session;begin_answering(t)
        t.answer(t.question.fallacy)
        self.assertEqual(t.stage,'OBJECTION_ANIMATION')
        self.assertEqual(t.animation_remaining,s.OBJECTION_DURATION)
        self.assertEqual(t.gadget_expression,'shocked')
        self.assertEqual(t.chef_expression,'surprised')
        t.continue_round()
        self.assertEqual(t.stage,'OBJECTION_ANIMATION')
        t.update(s.OBJECTION_DURATION)
        self.assertEqual(t.stage,'FEEDBACK')
        self.assertEqual(t.score,100)

    def test_exit_is_frozen_and_prepares_next_round_after_finishing(self):
        t=self.session;begin_answering(t)
        t.answer(t.question.fallacy);t.update(s.OBJECTION_DURATION)
        t.continue_round()
        self.assertEqual(t.stage,'BOARD_EXIT')
        positions=[x.position.copy() for x in t.targets]
        t.update(s.BOARD_EXIT_DURATION/2)
        self.assertEqual(t.number,1)
        self.assertEqual(positions,[x.position for x in t.targets])
        self.assertFalse(t.answer(t.question.fallacy))
        t.update(s.BOARD_EXIT_DURATION/2)
        self.assertEqual(t.stage,'READING')
        self.assertEqual(t.number,2)
        self.assertEqual(t.board_progress,0)
        self.assertEqual(t.animation_remaining,0)
        self.assertEqual(t.tint_alpha,0)

    def test_five_mistakes_show_feedback_before_exit_to_game_over(self):
        t=self.session
        for i in range(5):
            begin_answering(t);t.update(10)
            self.assertEqual(t.hp,80-20*i)
            self.assertEqual(t.stage,'MISTAKE_ANIMATION')
            t.update(t.banner_duration)
            self.assertEqual(t.stage,'FEEDBACK')
            t.continue_round();t.update(s.BOARD_EXIT_DURATION)
        self.assertEqual(t.stage,'GAME_OVER')
        self.assertEqual(t.counts['timeout'],5)

    def test_restart_clears_all_transition_and_result_state(self):
        t=self.session
        for stage in ('BOARD_ENTER','ANSWERING','OBJECTION_ANIMATION','MISTAKE_ANIMATION','FEEDBACK','BOARD_EXIT','GAME_OVER'):
            t.stage=stage;t.hp=0;t.animation_remaining=.8;t.transition_remaining=.2;t.tint_remaining=.4
            t.restart()
            self.assertEqual((t.hp,t.score,t.number),(100,0,1))
            self.assertEqual(t.stage,'READING')
            self.assertEqual(t.transition_remaining,0)
            self.assertEqual(t.animation_remaining,0)
            self.assertEqual(t.tint_alpha,0)
            self.assertEqual(t.board_progress,0)


class ArtworkAndInputTests(unittest.TestCase):
    def setUp(self):self.game=Game()
    def tearDown(self):pygame.quit()

    def click(self,point):return pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=point)

    def test_ready_and_banner_block_queued_clicks(self):
        g=self.game;t=g.session
        target=t.targets[0]
        g.frame([self.click(pygame.Rect(s.ACTION).center),self.click(target.rect.center)]*4,0)
        self.assertEqual(t.stage,'BOARD_ENTER')
        self.assertEqual(sum(t.counts.values()),0)
        g.frame([],s.BOARD_ENTER_DURATION)
        target=next(x for x in t.targets if x.fallacy_id!=t.question.fallacy)
        g.frame([self.click(target.rect.center),self.click(pygame.Rect(s.ACTION).center)]*4,0)
        self.assertEqual(t.stage,'MISTAKE_ANIMATION')
        self.assertEqual(t.hp,80)
        g.frame([self.click(pygame.Rect(s.ACTION).center)],.3)
        self.assertEqual(t.stage,'MISTAKE_ANIMATION')
        self.assertEqual(t.number,1)

    def test_frames_are_aligned_and_knife_white_highlights_survive(self):
        for strip in (self.game.scene_assets.knife,self.game.scene_assets.tomato):
            self.assertEqual(len(strip.frames),5)
            self.assertEqual(len({frame.get_size() for frame in strip.frames}),1)
            self.assertTrue(all(pygame.mask.from_surface(frame).count()>0 for frame in strip.frames))
        knife=self.game.scene_assets.knife.frames[0]
        self.assertGreater(pygame.mask.from_threshold(knife,(255,255,255,255),(25,25,25,1)).count(),0)
        self.assertEqual(SceneAssets.KNIFE_EXPRESSIONS,{'talking':2,'waiting':0,'shocked':3,'smug':1})

    def test_usable_board_rectangle_is_solid_wood_and_excludes_handle(self):
        board=self.game.scene_assets.board
        x,y,_,_=s.BOARD_RECT
        region=pygame.Rect(s.LABEL_REGION).move(-x,-y)
        wood=board.subsurface(region)
        self.assertEqual(pygame.mask.from_surface(wood).count(),region.width*region.height)
        self.assertEqual(board.get_at((0,0)).a,0)
        self.assertTrue(any(board.get_at((px,100)).a==0 for px in range(board.get_width()-170,board.get_width()-30)))

    def test_chef_is_visible_above_and_occluded_by_the_real_bench(self):
        g=self.game;g.frame([],0)
        self.assertEqual(g.screen.get_at((640,480)),g.scene_assets.background.get_at((640,480)))
        self.assertNotEqual(g.screen.get_at((640,333)),g.scene_assets.background.get_at((640,333)))

    def test_missing_scene_assets_keep_game_playable(self):
        with patch.object(s,'KNIFE_ASSET',Path('missing-knife.png')),patch.object(s,'BOARD_ASSET',Path('missing-board.jpg')),patch.object(s,'COURTROOM_ASSET',Path('missing-court.jpg')):
            assets=SceneAssets()
        self.assertFalse(assets.knife.frames)
        self.assertGreater(assets.board.get_width(),0)
        assets.draw_courtroom(self.game.screen,self.game.session)

    def test_banner_wording_can_be_changed(self):
        with patch.object(s,'WRONG_BANNER_TEXT','OBJECTION!'):
            begin_answering(self.game.session)
            self.game.session.answer(next(c for c in self.game.session.choices if c!=self.game.session.question.fallacy))
            self.game.frame([],s.BANNER_IN_DURATION)
            self.assertIn('OBJECTION!',self.game.scene.banner_cache)
            self.assertEqual(self.game.session.score,0)
