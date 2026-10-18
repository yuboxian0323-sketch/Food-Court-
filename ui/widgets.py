"""Provide shared typography, wrapping, buttons, and mouse-click predicates.

Operation:
    Share font metrics, wrapping, text placement, button drawing, and click predicates.
Input:
    Strings, colors, destination surfaces, scene-pixel geometry, and mouse events.
Output:
    UI pixels, wrapped text lines, or click booleans; no session updates.
"""
import pygame
import settings as s


class UI:
    """Cache fonts and draw shared text and basic controls in scene coordinates.

    Operation:
        Provide shared font caching, wrapping, typography, and basic controls.
    Input:
        Pygame surfaces, scene-pixel geometry, strings, and colors.
    Output:
        Renders UI or returns wrapped lines using cached fonts.
    """

    def __init__(self):
        """Create the fixed font sizes used by scenes and target rendering.

        Operation:
            Construct the fixed existing set of Pygame font sizes.
        Input:
            Initialized font subsystem.
        Output:
            Sets self.fonts; returns None.
        """
        self.fonts = {size: pygame.font.Font(None, size) for size in (20, 24, 26, 28, 32, 40, 48, 64, 80, 96)}

    def text(self, screen, text, pos, size=28, color=s.TEXT):
        """Blit one antialiased line with pos as its top-left scene-pixel coordinate.

        Operation:
            Render one antialiased line at its top-left scene coordinate.
        Input:
            screen, text, pos in pixels, size, color, and cached fonts.
        Output:
            Blits text; returns None.
        """
        screen.blit(self.fonts[size].render(text, True, color), pos)

    def centered_text(self, screen, text, center, size=28, color=s.TEXT):
        """Render text with its rectangle centered on scene-pixel coordinates.

        Operation:
            Render once and center the resulting rectangle at the given point.
        Input:
            screen, text, center in pixels, size, color, and cached fonts.
        Output:
            Blits centered text; returns None.
        """
        image = self.fonts[size].render(text, True, color)
        screen.blit(image, image.get_rect(center=center))

    def wrap(self, text, width, size=28):
        """Return pixel-width-limited lines while respecting explicit paragraph breaks.

        Operation:
            Wrap paragraphs by measured pixel width and split overlong words.
        Input:
            text, width in pixels, size, and cached fonts.
        Output:
            Returns lines preserving explicit paragraph breaks; no rendered output.
        """
        lines = []
        # Operation: Preserve explicit paragraph breaks before applying font-measured
        #     word wrapping.
        # Input: Text paragraphs, font metrics, and available pixel width.
        # Output: Wrapped lines retaining explicit paragraph boundaries.
        for paragraph in text.split('\n'):
            line = ''
            for word in paragraph.split():
                candidate = f'{line} {word}'.strip()
                if self.fonts[size].size(candidate)[0] > width:
                    if line:
                        lines.append(line)
                    line = word
                    # Operation: Also handle an unusually long word without spilling
                    #     out.
                    # Input: One word wider than the available measured width.
                    # Output: Fitting word fragments; text does not spill horizontally.
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
        """Draw wrapped lines at rect top-left using the selected font line spacing.

        Operation:
            Render wrapped lines with the existing font line spacing.
        Input:
            screen, text, rect origin/width, size, and color.
        Output:
            Blits lines without height clipping; returns None.
        """
        rect = pygame.Rect(rect)
        for i, line in enumerate(self.wrap(text, rect.width, size)):
            self.text(screen, line, (rect.x, rect.y + i * self.fonts[size].get_linesize()), size, color)

    def panel(self, screen, rect, color=s.PANEL):
        """Draw the legacy opaque rounded panel with its configured fill.

        Operation:
            Draw the existing opaque rounded rectangle.
        Input:
            screen, rect in pixels, and color.
        Output:
            Renders panel geometry; returns None.
        """
        pygame.draw.rect(screen, color, rect, border_radius=16)

    def button(self, screen, rect, label, enabled=True, color=None):
        """Draw a legacy button; enabled affects hover and text, not event routing.

        Operation:
            Draw the legacy button palette and delegate centered label text.
        Input:
            screen, rect, label, enabled, optional color, and mouse position.
        Output:
            Renders button; enabled affects hover/text only, not event routing; returns
            None.
        """
        rect = pygame.Rect(rect)
        hover = enabled and rect.collidepoint(pygame.mouse.get_pos())
        fill = color or ('#3b5263' if hover else '#293e4e')
        pygame.draw.rect(screen, fill, rect, border_radius=12)
        pygame.draw.rect(screen, s.ACCENT if hover else '#526575', rect, 2, border_radius=12)
        self.centered_text(screen, label, rect.center, 28, s.TEXT if enabled else s.MUTED)


def clicked(event, rect):
    """Return whether a left-button press lands in an integer scene-pixel rect.

    Operation:
        Check a left-button press against integer scene coordinates.
    Input:
        event and rect.
    Output:
        Returns bool; does not consume events or change game state.
    """
    return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and pygame.Rect(rect).collidepoint(event.pos)
