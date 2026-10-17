import pygame
import settings as s


class UI:
    def __init__(self):
        self.fonts = {size: pygame.font.Font(None, size) for size in (20, 24, 26, 28, 32, 40, 48, 64)}

    def text(self, screen, text, pos, size=28, color=s.TEXT):
        screen.blit(self.fonts[size].render(text, True, color), pos)

    def wrap(self, text, width, size=28):
        lines = []
        for paragraph in text.split('\n'):
            line = ''
            for word in paragraph.split():
                candidate = f'{line} {word}'.strip()
                if self.fonts[size].size(candidate)[0] > width:
                    if line:
                        lines.append(line)
                    line = word
                    # Also handle an unusually long word without spilling out.
                    while self.fonts[size].size(line)[0] > width:
                        cut = len(line) - 1
                        while self.fonts[size].size(line[:cut])[0] > width:
                            cut -= 1
                        lines.append(line[:cut])
                        line = line[cut:]
                else:
                    line = candidate
            lines.append(line)
        return lines

    def paragraph(self, screen, text, rect, size=28, color=s.TEXT):
        rect = pygame.Rect(rect)
        for i, line in enumerate(self.wrap(text, rect.width, size)):
            self.text(screen, line, (rect.x, rect.y + i * self.fonts[size].get_linesize()), size, color)

    def panel(self, screen, rect, color=s.PANEL):
        pygame.draw.rect(screen, color, rect, border_radius=16)

    def button(self, screen, rect, label, enabled=True, color=None):
        rect = pygame.Rect(rect)
        hover = enabled and rect.collidepoint(pygame.mouse.get_pos())
        fill = color or ('#3b5263' if hover else '#293e4e')
        pygame.draw.rect(screen, fill, rect, border_radius=12)
        pygame.draw.rect(screen, s.ACCENT if hover else '#526575', rect, 2, border_radius=12)
        image = self.fonts[28].render(label, True, s.TEXT if enabled else s.MUTED)
        screen.blit(image, image.get_rect(center=rect.center))


def clicked(event, rect):
    return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and pygame.Rect(rect).collidepoint(event.pos)
