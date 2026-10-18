"""Run the independent, illustrated fallacy dictionary.

Operation: Display two flash cards per book page with animated spread navigation.
Input: Original book and DictionaryCard PNG files in the project's assets folder.
Output: A standalone Pygame window; gameplay files and assets are never modified.
"""

import argparse
import math
from pathlib import Path

import pygame


ROOT = Path(__file__).resolve().parents[1]
SIZE = (1440, 1000)
CARDS_PER_PAGE = 2
CARDS_PER_SPREAD = CARDS_PER_PAGE * 2
TURN_SECONDS = 0.48


def load_art(path, min_alpha=1):
    """Load artwork and trim transparent margins without changing its source."""
    surface = pygame.image.load(str(path)).convert_alpha()
    return surface.subsurface(surface.get_bounding_rect(min_alpha=min_alpha)).copy()


def fit(surface, bounds):
    """Return an aspect-preserving image and its centered destination rectangle."""
    scale = min(bounds.width / surface.get_width(), bounds.height / surface.get_height())
    size = tuple(max(1, round(value * scale)) for value in surface.get_size())
    image = pygame.transform.smoothscale(surface, size)
    return image, image.get_rect(center=bounds.center)



class Dictionary:
    """Own dictionary navigation, page animation, and card enlargement."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
        pygame.display.set_caption('Food Court — Fallacy Dictionary')
        self.canvas = pygame.Surface(SIZE)
        self.font = pygame.font.SysFont('georgia', 35)
        self.small = pygame.font.SysFont('arial', 21)
        # Ignore faint export residue below the visible book when anchoring cards.
        self.book = load_art(ROOT / 'assets' / 'Dictionary.PNG', min_alpha=128)
        paths = sorted((ROOT / 'assets').glob('DictionaryCard[0-9][0-9].png'))
        if not paths:
            raise FileNotFoundError('No DictionaryCard PNG files were found in assets.')
        self.cards = [load_art(path) for path in paths]
        self.spread_count = math.ceil(len(self.cards) / CARDS_PER_SPREAD)
        self.spread = 0
        self.previous = 0
        self.direction = 0
        self.elapsed = TURN_SECONDS
        self.zoom = None
        self.hits = []
        self.prev_button = pygame.Rect(120, 920, 190, 48)
        self.next_button = pygame.Rect(1130, 920, 190, 48)
        self.close_button = pygame.Rect(1200, 90, 100, 44)
        self.book_image, self.book_rect = fit(self.book, pygame.Rect(55, 115, 1330, 790))
        self.spreads = [self.make_spread(index) for index in range(self.spread_count)]

    def text(self, text, center, color=(245, 232, 203), font=None, target=None):
        """Draw centered text on the requested surface."""
        image = (font or self.small).render(text, True, color)
        (target or self.canvas).blit(image, image.get_rect(center=center))

    def slots(self):
        """Calculate two vertically stacked cards per side, below the book's eyes."""
        # Input: Trimmed book bounds. Output: Card slots in logical screen coordinates.
        rect = self.book_rect
        for side in range(2):
            left = rect.x + rect.width * (0.045 if side == 0 else 0.535)
            top = rect.y + rect.height * 0.265
            width, height = rect.width * 0.42, rect.height * 0.67
            gap = 6
            cell_w, cell_h = width, (height - (CARDS_PER_PAGE - 1) * gap) / CARDS_PER_PAGE
            for row in range(CARDS_PER_PAGE):
                yield pygame.Rect(left, top + row * (cell_h + gap), cell_w, cell_h)

    def make_spread(self, index):
        """Compose a cached spread and record its visible card hit regions."""
        page = pygame.Surface(SIZE, pygame.SRCALPHA)
        page.blit(self.book_image, self.book_rect)
        hits = []
        for offset, slot in enumerate(self.slots()):
            card_id = index * CARDS_PER_SPREAD + offset
            if card_id >= len(self.cards):
                continue
            image, destination = fit(self.cards[card_id], slot.inflate(-2, -2))
            page.blit(image, destination)
            hits.append((destination, card_id))
        return page, hits

    def turn(self, direction):
        """Start a bounded spread transition; ignore input while already turning."""
        target = self.spread + direction
        if self.zoom is None and self.elapsed >= TURN_SECONDS and 0 <= target < self.spread_count:
            self.previous, self.spread = self.spread, target
            self.direction, self.elapsed = direction, 0.0

    def pointer(self, position):
        """Map resized-window coordinates to the aspect-preserving logical canvas."""
        width, height = self.screen.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        return ((position[0] - (width - SIZE[0] * scale) / 2) / scale,
                (position[1] - (height - SIZE[1] * scale) / 2) / scale)

    def event(self, event):
        """Handle navigation and modal card viewing without input passing through."""
        if event.type == pygame.KEYDOWN:
            if self.zoom is not None:
                if event.key == pygame.K_ESCAPE:
                    self.zoom = None
                return
            if event.key in (pygame.K_RIGHT, pygame.K_PAGEDOWN):
                self.turn(1)
            elif event.key in (pygame.K_LEFT, pygame.K_PAGEUP):
                self.turn(-1)
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        point = self.pointer(event.pos)
        if self.zoom is not None:
            if self.close_button.collidepoint(point) or not self.zoom_rect.collidepoint(point):
                self.zoom = None
            return
        if self.elapsed < TURN_SECONDS:
            return
        if self.prev_button.collidepoint(point):
            self.turn(-1)
        elif self.next_button.collidepoint(point):
            self.turn(1)
        else:
            for rect, card_id in self.spreads[self.spread][1]:
                if rect.collidepoint(point):
                    self.zoom = card_id
                    _, self.zoom_rect = fit(self.cards[card_id], pygame.Rect(140, 155, 1160, 690))
                    break

    def button(self, rect, label, enabled=True):
        """Render a navigation control with an explicit disabled appearance."""
        color = (106, 75, 49) if enabled else (55, 45, 37)
        pygame.draw.rect(self.canvas, color, rect, border_radius=12)
        self.text(label, rect.center, (255, 239, 204) if enabled else (129, 117, 101))

    def draw(self):
        """Render the book, a folding-page transition, and optional enlarged card."""
        self.canvas.fill((35, 28, 25))
        self.text('THE FALLACY DICTIONARY', (720, 57), font=self.font)
        self.text('Two cards per page • Click a card to read it', (720, 104))
        self.canvas.blit(self.spreads[self.spread][0], (0, 0))
        if self.elapsed < TURN_SECONDS:
            # Operation: Fold the old spread toward its spine, then unfold the new one.
            # Input: Transition progress and direction. Output: A narrowing page overlay.
            t = self.elapsed / TURN_SECONDS
            half = self.book_rect.width // 2
            spine = self.book_rect.centerx
            old_side = 1 if self.direction > 0 else 0
            side = old_side if t < 0.5 else 1 - old_side
            source = self.spreads[self.previous if t < 0.5 else self.spread][0]
            crop = pygame.Rect(spine if side else spine - half, self.book_rect.y,
                               half, self.book_rect.height)
            width = max(1, round(half * abs(math.cos(math.pi * t))))
            folded = pygame.transform.smoothscale(source.subsurface(crop), (width, crop.height))
            folded.fill((205, 190, 155, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.canvas.blit(folded, (spine if side else spine - width, crop.y))
        self.button(self.prev_button, '← Previous', self.spread > 0)
        self.button(self.next_button, 'Next →', self.spread < self.spread_count - 1)
        self.text(f'Spread {self.spread + 1} of {self.spread_count}  ·  ← / → to turn pages', (720, 945))
        if self.zoom is not None:
            veil = pygame.Surface(SIZE, pygame.SRCALPHA)
            veil.fill((12, 9, 7, 225))
            self.canvas.blit(veil, (0, 0))
            image, self.zoom_rect = fit(self.cards[self.zoom], pygame.Rect(140, 155, 1160, 690))
            self.canvas.blit(image, self.zoom_rect)
            self.button(self.close_button, 'Close ×')
            self.text('Esc or click outside the card to return to the book', (720, 905))
        image, destination = fit(self.canvas, self.screen.get_rect())
        self.screen.fill((20, 16, 14))
        self.screen.blit(image, destination)
        pygame.display.flip()

    def run(self):
        """Run the standalone window until closed, leaving game state untouched."""
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.event(event)
            self.elapsed = min(TURN_SECONDS, self.elapsed + dt)
            self.draw()
        pygame.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', type=Path, help='Save a still preview and exit.')
    args = parser.parse_args()
    viewer = Dictionary()
    if args.preview:
        viewer.draw()
        pygame.image.save(viewer.canvas, str(args.preview))
        pygame.quit()
    else:
        viewer.run()
