
import pygame
import settings


class Chef:
    def __init__(self, frame_duration=0.15):
        self.frames = []

        try:
            # Load the sprite sheet
            sheet = pygame.image.load(
                str(settings.ROOT / 'assets/Chef_SpriteSheet.png')
            ).convert_alpha()

            # Crop the three painted poses
            painted_width = 3187

            for index in range(3):
                left = round(index * painted_width / 3)
                right = round((index + 1) * painted_width / 3)

                cell = sheet.subsurface(
                    (left, 0, right - left, sheet.get_height())
                )

                frame = cell.subsurface(
                    cell.get_bounding_rect()
                ).copy()

                self.frames.append(frame)

            # Align frames to prevent the chef from jumping during animation
            width = max(frame.get_width() for frame in self.frames)
            height = max(frame.get_height() for frame in self.frames)

            aligned_frames = []

            for frame in self.frames:
                aligned = pygame.Surface(
                    (width, height), pygame.SRCALPHA
                )
                aligned.blit(
                    frame,
                    (
                        (width - frame.get_width()) // 2,
                        height - frame.get_height(),
                    ),
                )
                aligned_frames.append(aligned)

            self.frames = aligned_frames

        except (OSError, pygame.error, ValueError) as error:
            raise RuntimeError(
                f"Failed to load or process chef sprite sheet: {error}"
            ) from error

        self.current_frame = 0
        self.elapsed = 0.0
        self.frame_duration = frame_duration
        self.animating = False

    def play(self):
        self.current_frame = 0
        self.elapsed = 0.0
        self.animating = True

    def reset(self):
        self.current_frame = 0
        self.elapsed = 0.0
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

    def draw(self, screen, position=(108, 119), scale=1.0):
        # Select the current animation frame
        frame = self.frames[self.current_frame]

        # Resize the sprite if needed
        if scale != 1:
            frame = pygame.transform.smoothscale(
                frame,
                (
                    round(frame.get_width() * scale),
                    round(frame.get_height() * scale),
                ),
            )

        # Draw the chef on the screen
        screen.blit(frame, position)
