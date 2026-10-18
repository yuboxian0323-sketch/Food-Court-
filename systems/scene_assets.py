
import math
from functools import lru_cache
import pygame
import settings as s

from entities.tomato import Tomato
from entities.chef import Chef
from entities.character import SpriteStrip


class SceneAssets:
    KNIFE_EXPRESSIONS = {
        "talking": 2,
        "waiting": 0,
        "shocked": 3,
        "smug": 1,
    }

    def __init__(self):
        self.knife = SpriteStrip(s.KNIFE_ASSET)
        self.tomato = Tomato()
        self.chef = Chef()

        self.background = self.load_background()
        self.board = self.load_board()
        self.table = self.load_table()

        self.chef_expression = "listening"

        self.board_shadow = self.make_shadow(
            (s.BOARD_RECT[2], s.BOARD_RECT[3])
        )

    def load_background(self):
        source = pygame.image.load(str(s.COURTROOM_ASSET)).convert()
        scale = max(
            s.WIDTH / source.get_width(),
            s.HEIGHT / source.get_height(),
        )
        image = pygame.transform.smoothscale(
            source,
            (
                round(source.get_width() * scale),
                round(source.get_height() * scale),
            ),
        )

        result = pygame.Surface((s.WIDTH, s.HEIGHT))
        x = (image.get_width() - s.WIDTH) // 2
        y = (image.get_height() - s.HEIGHT) // 2
        result.blit(image, (0, 0), (x, y, s.WIDTH, s.HEIGHT))
        return result

    def load_board(self):
        source = pygame.image.load(str(s.BOARD_ASSET)).convert_alpha()
        width = s.BOARD_RECT[2]
        height = s.BOARD_RECT[3]
        return pygame.transform.smoothscale(source, (width, height))

    def load_table(self):
        source = pygame.image.load(str(s.TABLE_ASSET)).convert_alpha()
        width = s.FRONT_DESK_FOREGROUND[2]
        height = s.FRONT_DESK_FOREGROUND[3]
        return pygame.transform.smoothscale(source, (width, height))

    @staticmethod
    @lru_cache(maxsize=16)
    def make_shadow(size):
        width, height = size
        shadow = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 65), shadow.get_rect())
        return shadow

    def update_chef(self, dt, expression):
        if expression != self.chef_expression:
            self.chef_expression = expression
            if expression == "listening":
                self.chef.reset()
            else:
                self.chef.play()
        self.chef.update(dt)

    def draw_courtroom(self, screen, session):
        screen.blit(self.background, (0, 0))

        chef_width, chef_height = s.CHEF_PORTRAIT_SIZE
        chef_position = (
            s.CHEF_ANCHOR[0] - chef_width // 2,
            s.CHEF_ANCHOR[1] - chef_height,
        )
        self.chef.draw(screen, position=chef_position, scale=1.0)

        board_rect = pygame.Rect(s.BOARD_RECT)
        screen.blit(self.board_shadow, board_rect.move(0, 8))
        screen.blit(self.board, board_rect)

        if self.knife.frames:
            knife_frame = self.KNIFE_EXPRESSIONS.get(
                session.gadget_expression, 0
            )
            self.knife.draw(
                screen,
                knife_frame,
                s.KNIFE_ANCHOR,
                s.KNIFE_WIDTH,
            )

        self.tomato.draw(
            screen,
            hp=session.hp,
            anchor=s.TOMATO_ANCHOR,
            width=s.TOMATO_WIDTH,
            mistake=session.stage == "MISTAKE_ANIMATION",
            shake_time=session.banner_elapsed,
            shake_duration=session.banner_duration,
        )

        # Draw the table image in the foreground.
        desk = pygame.Rect(s.FRONT_DESK_FOREGROUND)
        screen.blit(self.table, desk.topleft)
