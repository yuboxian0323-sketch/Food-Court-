import os
import random
import unittest
from unittest.mock import patch
os.environ['SDL_VIDEODRIVER']='dummy'
import pygame
import settings as s
from game import Game
from entities.answer_target import update_targets


class SubpixelRenderingTests(unittest.TestCase):
    def setUp(self):
        self.game=Game()
        self.target=self.game.session.targets[0]
        self.renderer=self.game.scene.target_renderer
        self.canvas=pygame.Surface((s.WIDTH,s.HEIGHT))

    def tearDown(self):pygame.quit()

    def test_subpixel_step_changes_pixels_without_whole_pixel_jump(self):
        self.target.position.update(200.125,400.125)
        self.target.previous_position.update(self.target.position)
        self.target.accumulator=0
        images=[]
        whole_rects=[]
        with patch('pygame.mouse.get_pos',return_value=(-1,-1)):
            for _ in range(4):
                self.canvas.fill('#edf5ed')
                self.renderer.draw(self.canvas,self.target,2,'ANSWERING')
                images.append(pygame.image.tostring(self.canvas,'RGB'))
                whole_rects.append(self.target.rect.topleft)
                self.target.position.x+=.0625
                self.target.previous_position.update(self.target.position)
        self.assertEqual(len(set(whole_rects)),1)
        self.assertEqual(len(set(images)),4)

    def test_hit_edges_match_fractional_rendered_rectangle(self):
        self.target.position.update(200.25,400.5)
        self.target.previous_position.update(self.target.position)
        self.assertTrue(self.target.contains((200.25,400.5)))
        self.assertFalse(self.target.contains((200.2,400.5)))
        self.assertTrue(self.target.contains((200.25+self.target.width-.01,410)))
        self.assertFalse(self.target.contains((200.25+self.target.width,410)))

    def test_interpolation_between_ticks_is_continuous(self):
        target=self.target
        target.previous_position.update(200,400)
        target.position.update(200.25,400.125)
        points=[]
        for fraction in (0,.25,.5,.75,1):
            target.accumulator=s.MOTION_STEP*fraction
            points.append(target.draw_position)
        self.assertEqual(points[0],target.previous_position)
        self.assertEqual(points[-1],target.position)
        self.assertTrue(all(a.x<b.x for a,b in zip(points,points[1:])))

    def test_144_fps_does_not_hold_a_slow_target_on_whole_pixels(self):
        self.game.bank.rng=random.Random(42)
        session=self.game.session
        session.number=29
        session.next_round()
        session.acknowledge_unlock()
        session.ready()
        target=session.targets[0]
        holds=0
        previous=target.draw_position
        for _ in range(144):
            update_targets(session.targets,1/144)
            point=target.draw_position
            holds+=point==previous
            previous=point
        # The initial interpolated frame is deliberately one physics tick late.
        self.assertLessEqual(holds,2)
