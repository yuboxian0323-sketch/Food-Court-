import math
import os
import random
import unittest
from unittest.mock import patch
os.environ['SDL_VIDEODRIVER']='dummy'
import pygame
import settings as s
from entities.answer_target import make_targets,update_targets
from systems.question_bank import QuestionBank


class SharedAnswerBoxTests(unittest.TestCase):
    def setUp(self):self.bank=QuestionBank(s.ROOT/'data')

    def test_all_choices_share_entire_box_and_start_at_double_cruise_speed(self):
        for count in (2,8):
            ts=make_targets(list(self.bank.fallacies)[:count],self.bank.fallacies,random.Random(42))
            factor=1 if count==2 else s.DENSE_SPEED_FACTOR
            for t in ts:
                self.assertEqual(t.bounds,s.LABEL_REGION)
                self.assertGreaterEqual(t.speed,28*factor)
                self.assertLessEqual(t.speed,36*factor)
            headings={round(math.atan2(t.velocity.y,t.velocity.x),1) for t in ts}
            self.assertGreaterEqual(len(headings),count-1)
            self.assertTrue(any(abs(t.velocity.y)>2 for t in ts))

    def test_head_on_labels_curve_or_yield_without_touching_or_jumping(self):
        ts=make_targets(list(self.bank.fallacies)[:2],self.bank.fallacies,random.Random(9))
        bx,by,bw,bh=s.LABEL_REGION
        positions=[(bx+12,by+bh/2),(bx+bw-ts[1].width-12,by+bh/2)]
        for t,pos,heading in zip(ts,positions,[0,math.pi]):
            t.position.update(pos);t.previous_position.update(pos)
            t.heading=heading;t.speed=32;t.velocity.update(math.cos(heading)*32,math.sin(heading)*32)
            t.avoidance_axes.clear()
        paths=[[] for _ in ts]
        for _ in range(600):
            before=[t.position.copy() for t in ts]
            update_targets(ts,1/60)
            self.assertFalse(ts[0].rect.inflate(12,12).colliderect(ts[1].rect))
            for t,pos,path in zip(ts,before,paths):
                self.assertLess(t.position.distance_to(pos),.75)
                path.append(tuple(t.position))
        self.assertTrue(any(max(p[1] for p in path)-min(p[1] for p in path)>20 for path in paths))

    def test_targets_cross_shared_board_midline_in_both_directions(self):
        ts=make_targets(list(self.bank.fallacies)[:2],self.bank.fallacies,random.Random(2))
        bx,by,bw,bh=s.LABEL_REGION
        midline=by+(bh-ts[0].height)/2
        positions=[(bx+12,midline-45),(bx+bw-ts[1].width-12,midline+45)]
        for t,pos,heading in zip(ts,positions,[math.pi/2,-math.pi/2]):
            t.position.update(pos);t.previous_position.update(pos)
            t.heading=heading;t.speed=32;t.velocity.update(0,32 if heading>0 else -32)
            t.steering=t.steering_target=0;t.avoidance_axes.clear()
        paths=[[] for _ in ts]
        with patch.object(s,'WANDER_STRENGTH',0):
            for _ in range(600):
                update_targets(ts,1/60)
                for t,path in zip(ts,paths):path.append(tuple(t.position))
        self.assertGreater(max(p[1] for p in paths[0]),midline+10)
        self.assertLess(min(p[1] for p in paths[1]),midline-10)
        self.assertTrue(all(t.bounds_corrections==0 for t in ts))
