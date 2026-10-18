"""Retain the legacy three-frame Chef player loaded during game startup.

Operation:
    Retain the separately loaded legacy three-frame Chef interface.
Input:
    Chef sheet path and optional play/update/draw calls.
Output:
    Extracted source frames and legacy animation state; the court uses its existing
    drawn portrait.
"""
import pygame


class Chef:
    """Keep the legacy equal-width three-frame sprite animation interface.

    Operation:
        Retain the legacy three-frame animation interface loaded at startup.
    Input:
        Sprite-sheet path and later play/update/draw calls.
    Output:
        Owns source-sized frames; visible court portraits still come from SceneAssets.
    """

    def __init__(self, sprite_sheet_path):
        """Load three horizontal cells from sprite_sheet_path using source alpha.

        Operation:
            Load alpha artwork and divide it into three equal horizontal cells.
        Input:
            sprite_sheet_path and an initialized Pygame display.
        Output:
            Sets frames, current_frame, timer, and animating. Load/format errors
            propagate.
        """
        sheet = pygame.image.load(sprite_sheet_path).convert_alpha()

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
        """Start the animation from the first frame.

        Operation:
            Reset the legacy animation to its first frame.
        Input:
            Current Chef instance.
        Output:
            Sets current_frame/elapsed to zero and animating to True; returns None.
        """
        self.current_frame = 0
        self.elapsed = 0
        self.animating = True

    def update(self, dt):
        """Advance the animation based on elapsed time.

        Operation:
            Advance one legacy frame when its externally supplied duration elapses.
        Input:
            dt: seconds; animating/elapsed; frame_duration supplied by a caller.
        Output:
            Updates frame index/elapsed and stops at the last frame; returns None.
            Missing frame_duration can raise AttributeError; this pre-existing contract
            is retained.
        """
        if not self.animating:
            return

        self.elapsed += dt

        if self.elapsed >= self.frame_duration:
            self.elapsed -= self.frame_duration
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                self.current_frame = len(self.frames) - 1
                self.animating = False

    def draw(self, screen, anchor):
        """Blit the current source-sized frame at a midbottom scene-pixel anchor.

        Operation:
            Align the selected source frame to a midbottom baseline.
        Input:
            screen, anchor: scene pixels; current_frame and frames.
        Output:
            Blits the current frame; returns None.
        """
        x, floor = anchor
        image = self.frames[self.current_frame]

        rect = image.get_rect(midbottom=(x, floor))
        screen.blit(image, rect)
