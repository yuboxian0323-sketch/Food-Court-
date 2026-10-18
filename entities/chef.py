
import pygame


class Chef:
    def __init__(self, sprite_sheet_path, frame_duration=0.15):
        sheet = pygame.image.load(str(sprite_sheet_path)).convert_alpha()

        print("Sheet size:", sheet.get_size())
        print("Frame width:", sheet.get_width() // 3)
        print("Frame height:", sheet.get_height())

        # Three equally sized frames arranged horizontally.
        frame_width = sheet.get_width() // 3
        frame_height = sheet.get_height()

        self.frames = [
            sheet.subsurface(
                (i * frame_width, 0, frame_width, frame_height)
            ).copy()
            for i in range(3)
        ]

        self.current_frame = 0
        self.elapsed = 0
        self.frame_duration = frame_duration
        self.animating = False

    def play(self):
        """Start the animation from the first frame."""
        self.current_frame = 0
        self.elapsed = 0
        self.animating = True

    def reset(self):
        """Return to the first frame and stop the animation."""
        self.current_frame = 0
        self.elapsed = 0
        self.animating = False

    def update(self, dt):
        """Play the three frames once, then hold the final frame."""
        if not self.animating:
            return

        self.elapsed += dt

        while self.elapsed >= self.frame_duration and self.animating:
            self.elapsed -= self.frame_duration
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                self.current_frame = len(self.frames) - 1
                self.animating = False

    def draw(self, screen, anchor, size=None):
        image = self.frames[self.current_frame]

        if size:
            image = pygame.transform.smoothscale(image, size)

        screen.blit(image, image.get_rect(midbottom=anchor))
