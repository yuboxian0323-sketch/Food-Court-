
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
        self.table = self.load_table()

        self.chef_expression = "listening"

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

    def load_table(self):
        source = pygame.image.load(str(s.TABLE_ASSET)).convert_alpha()
        bounds = source.get_bounding_rect()
        source = source.subsurface(bounds).copy()
        width = s.FRONT_DESK_FOREGROUND[2]
        height = round(source.get_height() * width / source.get_width())
        return pygame.transform.smoothscale(source, (width, height))

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

        frame_width, frame_height = self.chef.frames[0].get_size()
        portrait_width, portrait_height = s.CHEF_PORTRAIT_SIZE
        chef_scale = min(
            portrait_width / frame_width,
            portrait_height / frame_height,
        )
        chef_width = round(frame_width * chef_scale)
        chef_height = round(frame_height * chef_scale)
        chef_position = (
            s.CHEF_ANCHOR[0] - chef_width // 2,
            s.CHEF_ANCHOR[1] - chef_height // 2,
        )
        self.chef.draw(screen, position=chef_position, scale=chef_scale)

        # Draw the table before the foreground characters so they stay on top.
        desk = pygame.Rect(s.FRONT_DESK_FOREGROUND)
        screen.blit(self.table, desk.topleft)

        if self.knife.frames:
            knife_frame = self.KNIFE_EXPRESSIONS.get(
                session.gadget_expression, 0
            )
            knife_scale = s.KNIFE_WIDTH / self.knife.frames[knife_frame].get_width()
            self.knife.draw(
                screen,
                knife_frame,
                s.KNIFE_ANCHOR,
                knife_scale,
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
