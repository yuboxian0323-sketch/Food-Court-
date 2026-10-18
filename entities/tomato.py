
import math

import pygame
import settings as s
from systems.expressions import TOMATO_FRAMES, tomato_expression_for_hp


class Tomato:
    def __init__(self):
        self.frames = []

        sheet = pygame.image.load(
            str(s.TOMATO_ASSET)
        ).convert_alpha()

        # Five frames arranged horizontally.
        frame_bounds = [
            (2, 1116),
            (1119, 2232),
            (2237, 3351),
            (3353, 4468),
            (4469, 5585),
        ]

        for left, right in frame_bounds:
            frame = sheet.subsurface(
                (left, 0, right - left, sheet.get_height())
            ).copy()

            self.frames.append(
                pygame.transform.smoothscale(frame, (220, 202))
            )

    def draw(
        self,
        screen,
        hp,
        anchor,
        width=220,
        mistake=False,
        shake_time=0,
        shake_duration=1,
    ):
        # Choose the expression inside Tomato.
        if mistake:
            frame_index = 4
        else:
            expression = tomato_expression_for_hp(hp)
            frame_index = TOMATO_FRAMES[expression]

        frame = self.frames[frame_index]

        # Resize while keeping the image's aspect ratio.
        height = round(frame.get_height() * width / frame.get_width())
        frame = pygame.transform.smoothscale(frame, (width, height))

        # Shake the tomato during the mistake animation.
        x, y = anchor

        if mistake and shake_duration > 0:
            decay = max(0, 1 - shake_time / shake_duration)
            x += round(math.sin(shake_time * 48) * 7 * decay)
            y += round((math.cos(shake_time * 48) - 1) * 2 * decay)

        # Anchor represents the bottom-center of the tomato.
        position = (x - width // 2, y - height)

        screen.blit(frame, position)
