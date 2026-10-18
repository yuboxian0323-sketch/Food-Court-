import asyncio
import time
import pygame
import settings as s
from scenes.base import Scene
from systems.question_bank import QuestionBank, ContentError
from systems.session import Session
from entities.tomato import Tomato
from systems.scene_assets import SceneAssets
from ui.widgets import UI


class ErrorScene(Scene):
    def __init__(self, game, message):
        self.game, self.message = game, message

    def draw(self, screen):
        screen.fill(s.BG)
        self.game.ui.text(screen, 'Content needs a quick fix', (60, 70), 48, s.ACCENT)
        self.game.ui.paragraph(screen, self.message, (60, 160, 1150, 350), 28)
        self.game.ui.text(screen, 'Fix the JSON file, then restart the game. Close the window to quit.', (60, 620), 28)


class Game:

    def __init__(self):
        pygame.display.init()
        pygame.font.init()

        # Set up the display and game state
        self.screen = pygame.display.set_mode((s.WIDTH, s.HEIGHT)) #Window size
        pygame.display.set_caption('Food Court')
        self.running = True
        self.ui = UI()

        try:
            self.scene_assets = SceneAssets()
            self.bank = QuestionBank(s.ROOT / 'data')
            self.session = Session(self.bank)
            from scenes.court import Court
            self.scene = Court(self)
        except ContentError as error:
            self.scene = ErrorScene(self, str(error))

    def restart(self):
        self.session.restart()
        from scenes.court import Court
        self.scene = Court(self)
        self.scene.transitioned = True

    def frame(self, events, dt):
        """Process one event batch before advancing and drawing the active scene.

        Operation:
            Dispatch events before updating time, then draw the resulting current scene.
        Input:
            events: ordered event batch; dt: elapsed seconds; running/current scene.
        Output:
            Updates state and flips the display; returns None. Quit stops processing;
            scene replacement blocks queued click-through.
        """
        scene = self.scene
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif scene is self.scene:
                scene.handle_event(event)
        if not self.running:
            return
        # Operation: A scene may change during update; always draw the resulting current
        #     scene.
        # Input: Current scene after event dispatch and dt seconds.
        # Output: Updates once and draws the resulting current scene before flipping.
        self.scene.update(dt)
        self.scene.draw(self.screen)
        pygame.display.flip()

    async def run(self):
        """Run until quit with perf_counter seconds and absolute frame deadlines.

        Operation:
            Pace frames with perf_counter seconds and absolute deadlines.
        Input:
            Pygame events, configured FPS, running flag, and current scene.
        Output:
            Updates the desktop window until quit; releases Pygame in finally; coroutine
            returns None.
        """
        previous=time.perf_counter()
        deadline=previous
        try:
            while self.running:
                now=time.perf_counter()
                dt=now-previous
                previous=now
                self.frame(pygame.event.get(),dt)
                await asyncio.sleep(0)
                # Operation: Absolute deadlines avoid adding sleep overshoot to every
                #     following frame. perf_counter avoids millisecond quantization.
                # Input: Monotonic clock, target FPS, and prior deadline.
                # Output: Schedules the next frame without accumulating ordinary sleep
                #     overshoot.
                deadline+=1/s.FPS
                remaining=deadline-time.perf_counter()
                if remaining>0:
                    await asyncio.sleep(remaining)
                elif remaining < -1/s.FPS:
                    deadline=time.perf_counter()
        finally:
            pygame.quit()


class Game():
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((s.WIDTH, s.HEIGHT))
        pygame.display.set_caption(s.TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

    async def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            await asyncio.sleep(0)  # Yield control to the event loop
            self.clock.tick(s.FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        # Update game state here
        pass

    def draw(self):
        self.screen.fill(s.BACKGROUND_COLOR)
        # Draw game elements here
        pygame.display.flip()


if __name__ == '__main__':
    asyncio.run(Game().run())
