"""Small drawn stand-ins for missing Chef and gadget art, with clear reactions."""
import pygame

INK = '#263b4d'


def eyes(screen, center, expression):
    x, y = center
    for offset in (-15, 15):
        pygame.draw.circle(screen, INK, (x+offset, y), 4)
    if expression in ('shocked', 'surprised'):
        pygame.draw.ellipse(screen, INK, (x-7, y+13, 14, 19), 3)
    elif expression == 'stern':
        pygame.draw.line(screen, INK, (x-15, y+20), (x+15, y+20), 3)
        pygame.draw.line(screen, INK, (x-23, y-11), (x-8, y-6), 3)
        pygame.draw.line(screen, INK, (x+8, y-6), (x+23, y-11), 3)
    elif expression == 'smug':
        pygame.draw.line(screen, INK, (x-22,y-2), (x-9,y-2), 3)
        pygame.draw.line(screen, INK, (x+7,y-12), (x+24,y-16), 3)
        pygame.draw.arc(screen, INK, (x-10,y+5,30,20), 3.3, 6, 3)
    elif expression == 'talking':
        pygame.draw.ellipse(screen, INK, (x-10, y+13, 20, 12), 2)
    else:
        pygame.draw.arc(screen, INK, (x-15, y+5, 30, 20), 3.2, 6.1, 3)



def _draw_gadget(screen, anchor, expression):
    x, floor = anchor
    pygame.draw.rect(screen, '#91a6b6', (x-11, floor-64, 22, 64), border_radius=8)
    for width in (100, 70, 40):
        pygame.draw.ellipse(screen, '#59778c', (x-width//2, floor-190, width, 140), 3)
    pygame.draw.ellipse(screen, '#d8e4e9', (x-43, floor-147, 86, 74))
    eyes(screen, (x, floor-127), expression)
    pygame.draw.rect(screen, '#a37852', (x-75, floor-10, 150, 10), border_radius=3)



def draw_gadget(screen, anchor, expression):
    portrait=pygame.Surface((180,220),pygame.SRCALPHA)
    _draw_gadget(portrait,(90,220),expression)
    portrait=pygame.transform.smoothscale(portrait,(90,110))
    screen.blit(portrait,(anchor[0]-45,anchor[1]-110))
