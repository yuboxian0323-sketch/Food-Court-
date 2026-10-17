from helpers import begin_answering, finish_result, ready_frame
import copy
import math
import os
import random
import unittest
from unittest.mock import patch
os.environ['SDL_VIDEODRIVER']='dummy'
import pygame
import settings as s
from entities.answer_target import make_targets, update_targets
from systems.question_bank import QuestionBank
from game import Game


class WanderTests(unittest.TestCase):
    def setUp(self):
        self.bank=QuestionBank(s.ROOT/'data',random.Random(1))

    def targets(self,count,seed):
        return make_targets(list(self.bank.fallacies)[:count],self.bank.fallacies,random.Random(seed))

    def test_full_round_continuity_padding_gap_and_no_safeguard_corrections(self):
        for count in range(2,9):
            for seed in range(4):
                targets=self.targets(count,seed)
                paths=[[] for _ in targets]
                for _ in range(600):
                    before=[(t.position.copy(),t.velocity.copy(),t.turn_rate) for t in targets]
                    update_targets(targets,1/60)
                    for target,(pos,vel,rate),path in zip(targets,before,paths):
                        self.assertLessEqual(target.position.distance_to(pos),target.speed*1.3/60+1e-6)
                        self.assertLessEqual(target.velocity.distance_to(vel)*60,s.MAX_ACCELERATION+1e-6)
                        self.assertLessEqual(target.velocity.length(),target.speed*1.3)
                        self.assertLessEqual(abs(target.turn_rate),s.MAX_TURN_RATE+1e-6)
                        self.assertLessEqual(abs(target.turn_rate-rate)*60,s.MAX_ANGULAR_ACCELERATION+1e-6)
                        self.assertTrue(pygame.Rect(s.LABEL_REGION).contains(target.rect))
                        left,top,right,bottom=target.limits
                        self.assertTrue(left-1e-7<=target.position.x<=right+1e-7)
                        self.assertTrue(top-1e-7<=target.position.y<=bottom+1e-7)
                        path.append(tuple(target.position))
                    for i,t in enumerate(targets):
                        for other in targets[i+1:]:
                            self.assertFalse(t.rect.inflate(s.TARGET_READABILITY_GAP,s.TARGET_READABILITY_GAP).colliderect(other.rect))
                self.assertTrue(all(t.bounds_corrections==0 for t in targets),(count,seed))
                for path in paths:
                    self.assertGreater(max(p[0] for p in path)-min(p[0] for p in path),5)
                    self.assertGreater(max(p[1] for p in path)-min(p[1] for p in path),2)

    def test_30_60_144_fps_match_in_both_axes(self):
        for count in (2,8):
            results=[]
            for fps in (30,60,144):
                targets=self.targets(count,42)
                for _ in range(10*fps):update_targets(targets,1/fps)
                results.append(targets)
            for a,b,c in zip(*results):
                self.assertLess(a.position.distance_to(b.position),1e-6)
                self.assertLess(b.position.distance_to(c.position),1e-6)
                self.assertLess(a.velocity.distance_to(c.velocity),1e-6)

    def test_slow_frame_is_bounded_and_stationary_setting_freezes(self):
        targets=self.targets(8,11)
        before=[t.position.copy() for t in targets]
        update_targets(targets,20)
        for target,pos in zip(targets,before):
            self.assertLessEqual(target.position.distance_to(pos),s.MOTION_MAX_CATCHUP*target.speed*1.3+1e-6)
        before=copy.deepcopy(targets)
        with patch.object(s,'LABEL_SPEED_MULTIPLIER',0):update_targets(targets,1)
        for target,old in zip(targets,before):
            self.assertEqual(target.position,old.position)
            self.assertEqual(target.velocity,old.velocity)
            self.assertEqual(target.steering,old.steering)

    def test_hover_does_not_change_simulation_and_click_uses_drawn_rect(self):
        game=Game()
        try:
            begin_answering(game.session)
            targets=game.session.targets
            for _ in range(90):update_targets(targets,1/60)
            original=copy.deepcopy(targets)
            target=targets[0]
            with patch('pygame.mouse.get_pos',return_value=target.rect.center):
                game.scene.draw(game.screen)
            for t,old in zip(targets,original):
                self.assertEqual(t.position,old.position)
                self.assertEqual(t.velocity,old.velocity)
            click=pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=target.rect.center)
            game.frame([click]*4,1/60)
            self.assertEqual(sum(game.session.counts.values()),1)
            self.assertEqual(game.session.selected,target.fallacy_id)
            before=[t.position.copy() for t in targets]
            game.frame([],1/60)
            self.assertEqual(before,[t.position for t in targets])
        finally:pygame.quit()
