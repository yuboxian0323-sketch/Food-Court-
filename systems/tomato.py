"""Use only the supplied art; discard the sprite sheet's transparent tail."""
import pygame
import settings


class Tomato:
    def __init__(self):
        self.frames = []
        try:
            sheet = pygame.image.load(str(settings.ROOT / 'assets/Tomato_SpriteSheet.png')).convert_alpha()
            # The supplied sheet has five painted expressions, not 11 square cells.
            for left, right in ((2, 1116), (1119, 2232), (2237, 3351), (3353, 4468), (4469, 5585)):
                frame = sheet.subsurface((left, 0, right-left, sheet.get_height()))
                self.frames.append(pygame.transform.smoothscale(frame, (220, 202)))
        except (OSError, pygame.error, ValueError):
            pass

    def draw(self, screen, hp, result=None, position=(108, 119), scale=1.0):
        if self.frames:
            index = 0 if hp >= settings.FACE_NORMAL_MIN_HP else 2 if hp >= settings.FACE_NERVOUS_MIN_HP else 3
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
