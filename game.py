
"""Manage the game window, session, scenes, and main loop."""

import asyncio
import time

import pygame
import settings as s

from scenes.base import Scene
from systems.question_bank import QuestionBank, ContentError
from systems.scene_assets import SceneAssets
from systems.session import Session
from ui.widgets import UI


class ErrorScene(Scene):
    """Display content validation errors."""

    def __init__(self, game, message):
        self.game = game
        self.message = message

    def draw(self, screen):
        screen.fill(s.BG)
        self.game.ui.text(
            screen, "Content needs a quick fix", (60, 70), 48, s.ACCENT
        )
        self.game.ui.paragraph(
            screen, self.message, (60, 160, 1150, 350), 28
        )
        self.game.ui.text(
            screen,
            "Fix the JSON file, then restart the game. Close the window to quit.",
            (60, 620),
            28,
        )


class Game:
    """Manage game state and the asynchronous main loop."""

    def __init__(self):
        pygame.display.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((s.WIDTH, s.HEIGHT))
        pygame.display.set_caption("Food Court")

        self.running = True
        self.ui = UI()

        try:
            self.scene_assets = SceneAssets()
            self.bank = QuestionBank(s.ROOT / "data")
            self.session = Session(self.bank)

            from scenes.court import Court

            self.scene = Court(self)

        except ContentError as error:
            self.scene = ErrorScene(self, str(error))

    def restart(self):
        """Restart the session and return to the court scene."""
        self.session.restart()

        from scenes.court import Court

        self.scene = Court(self)
        self.scene.transitioned = True

    def frame(self, events, dt):
        """Handle events, update the scene, and render one frame."""
        scene = self.scene

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif scene is self.scene:
                scene.handle_event(event)

        if not self.running:
            return

        self.scene.update(dt)
        self.scene.draw(self.screen)
        pygame.display.flip()

    async def run(self):
        """Run the game at the configured frame rate."""
        previous = time.perf_counter()
        deadline = previous

        try:
            while self.running:
                now = time.perf_counter()
                dt = now - previous
                previous = now

                self.frame(pygame.event.get(), dt)
                await asyncio.sleep(0)

                deadline += 1 / s.FPS
                remaining = deadline - time.perf_counter()

                if remaining > 0:
                    await asyncio.sleep(remaining)
                elif remaining < -1 / s.FPS:
                    deadline = time.perf_counter()

        finally:
            pygame.quit()


if __name__ == "__main__":
    asyncio.run(Game().run())
