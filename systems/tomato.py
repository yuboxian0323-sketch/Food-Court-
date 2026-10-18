"""Use only the supplied art; discard the sprite sheet's transparent tail.

Operation:
    Retain original legacy Tomato crops, HP selection, and missing-art geometry.
Input:
    Tomato sheet, HP, destination surface, top-left position, and optional scale.
Output:
    Legacy frames and rendered output; source art and gameplay state remain unchanged.
"""
import pygame
import settings
from systems.expressions import TOMATO_FRAMES, tomato_expression_for_hp


class Tomato:
    """Retain the legacy cropped Tomato renderer and missing-art fallback.

    Operation:
        Retain the legacy five-crop renderer and its existing drawn fallback.
    Input:
        Configured Tomato sheet and later draw parameters.
    Output:
        Owns legacy-size expression frames; court uses a different preserved renderer.
    """

    def __init__(self):
        """Extract the original five individual crop ranges without changing source art.

        Operation:
            Extract the five original crop ranges and scale each to the legacy size.
        Input:
            Tomato asset path and initialized display.
        Output:
            Sets frames; caught read/format/crop failures retain the existing fallback
            route.
        """
        self.frames = []
        try:
            sheet = pygame.image.load(str(settings.ROOT / 'assets/Tomato_SpriteSheet.png')).convert_alpha()
            # Operation: The supplied sheet has five painted expressions, not 11 square
            #     cells.
            # Input: Legacy Tomato sheet and original five painted crop ranges.
            # Output: Five separately scaled legacy frames; no source pixels are
            #     changed.
            for left, right in ((2, 1116), (1119, 2232), (2237, 3351), (3353, 4468), (4469, 5585)):
                frame = sheet.subsurface((left, 0, right-left, sheet.get_height()))
                self.frames.append(pygame.transform.smoothscale(frame, (220, 202)))
        except (OSError, pygame.error, ValueError):
            pass

    def draw(self, screen, hp, result=None, position=(108, 119), scale=1.0):
        """Draw an HP-selected frame at a top-left position with optional scaling.

        Operation:
            Select by shared HP thresholds, apply optional scaling, and draw at
            top-left.
        Input:
            screen, hp, position in pixels, scale; result is accepted but unused.
        Output:
            Blits art or legacy fallback geometry; returns None; crop and rounding
            behavior are retained.
        """
        # Operation: Legacy crop sizes differ from SceneAssets; preserve their original
        #     appearance.
        # Input: Loaded legacy frames or missing-art state plus HP.
        # Output: Existing cropped artwork or fallback geometry; no renderer
        #     substitution.
        if self.frames:
            index = TOMATO_FRAMES[tomato_expression_for_hp(hp)]
            frame = self.frames[index]
        else:
            frame = pygame.Surface((220,202),pygame.SRCALPHA)
            pygame.draw.circle(frame, '#ce5438', (110,105), 88)
            pygame.draw.polygon(frame, '#63864c', [(110,5),(85,42),(135,42)])
            for x in (80,140):
                pygame.draw.circle(frame, '#273c4e', (x,88), 6)
            if hp < settings.FACE_NERVOUS_MIN_HP:
                pygame.draw.ellipse(frame, '#273c4e', (96,120,28,32), 3)
            else:
                pygame.draw.line(frame, '#273c4e', (88,135),(132,135),3)
        if scale != 1:
            frame = pygame.transform.smoothscale(frame,(round(frame.get_width()*scale),round(frame.get_height()*scale)))
        screen.blit(frame, position)
