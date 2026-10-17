# chef.py
import pygame


import pygame


class Chef:
    def __init__(self, sprite_sheet_path):
        sheet = pygame.image.load(sprite_sheet_path).convert_alpha()

        # Assuming 3 equally sized frames arranged horizontally
        frame_width = sheet.get_width() // 3
        frame_height = sheet.get_height()

        self.frames = [
            sheet.subsurface(
                (i * frame_width, 0, frame_width, frame_height)
            ).copy()
            for i in range(3)
        ]

        self.current_frame = 0
        self.timer = 0
        self.animating = False
        

    def play(self):
        """Start the animation from the first frame."""
        self.current_frame = 0
        self.elapsed = 0
        self.animating = True

    def update(self, dt):
        """Advance the animation based on elapsed time."""
        if not self.animating:
            return

        self.elapsed += dt

        if self.elapsed >= self.frame_duration:
            self.elapsed -= self.frame_duration
            self.current_frame += 1

            # Stop after playing all three frames.
            if self.current_frame >= len(self.frames):
                self.current_frame = len(self.frames) - 1
                self.animating = False

    def draw(self, screen, anchor):
        x, floor = anchor
        image = self.frames[self.current_frame]

        # Center the sprite horizontally and align it to the floor.
        rect = image.get_rect(midbottom=(x, floor))
        screen.blit(image, rect)