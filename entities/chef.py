"""Load and animate the three Chef poses from the supplied sprite sheet."""
import pygame


class Chef:
    def __init__(self, sprite_sheet_path, frame_duration=0.15):
        sheet = pygame.image.load(str(sprite_sheet_path)).convert_alpha()

        # The three painted poses occupy the leftmost 3187 pixels; the rest
        # of this sheet is transparent.
        painted_width = 3187
        frames = []
        for index in range(3):
            left = round(index * painted_width / 3)
            right = round((index + 1) * painted_width / 3)
            cell = sheet.subsurface(
                (left, 0, right - left, sheet.get_height())
            )
            frames.append(cell.subsurface(cell.get_bounding_rect()).copy())

        width = max(frame.get_width() for frame in frames)
        height = max(frame.get_height() for frame in frames)
        self.frames = []
        for frame in frames:
            aligned = pygame.Surface((width, height), pygame.SRCALPHA)
            aligned.blit(
                frame,
                ((width - frame.get_width()) // 2, height - frame.get_height()),
            )
            self.frames.append(aligned)

        self.current_frame = 0
        self.elapsed = 0.0
        self.frame_duration = frame_duration
        self.animating = False

    def play(self):
        self.current_frame = 0
        self.elapsed = 0
        self.animating = True

    def reset(self):
        self.current_frame = 0
        self.elapsed = 0
        self.animating = False

    def update(self, dt):
        if not self.animating:
            return

        self.elapsed += max(0, dt)
        while self.elapsed >= self.frame_duration and self.animating:
            self.elapsed -= self.frame_duration
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                self.current_frame = len(self.frames) - 1
                self.animating = False

    def draw(self, screen, anchor, size=None):
        image = self.frames[self.current_frame]
        if size:
            scale = min(size[0] / image.get_width(), size[1] / image.get_height())
            scaled_size = (
                round(image.get_width() * scale),
                round(image.get_height() * scale),
            )
            image = pygame.transform.smoothscale(image, scaled_size)
        screen.blit(image, image.get_rect(midbottom=anchor))
