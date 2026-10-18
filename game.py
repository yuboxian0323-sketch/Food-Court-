"""Own the desktop window, scene dispatch, and asynchronous frame pacing.

Operation:
    Initialize resources and dispatch the asynchronous desktop scene loop.
Input:
    Configured assets/content, Pygame events, and monotonic elapsed seconds.
Output:
    Window/rendering and session state; content failures become an error scene.
"""
import asyncio
import time
import pygame
import settings as s
from scenes.base import Scene
from systems.question_bank import QuestionBank, ContentError
from systems.session import Session
from systems.tomato import Tomato
from systems.scene_assets import SceneAssets
from ui.widgets import UI


class ErrorScene(Scene):
    """Display content validation failures instead of entering the court.

    Operation:
        Retain a readable content-validation diagnostic for rendering.
    Input:
        Application reference and validation message.
    Output:
        Provides the error scene drawing hook.
    """

    def __init__(self, game, message):
        """Store the application and the content diagnostic to display.

        Operation:
            Bind the diagnostic to the application UI.
        Input:
            game and message from failed content validation.
        Output:
            Stores game/message; returns None.
        """
        self.game, self.message = game, message

    def draw(self, screen):
        """Draw the content error and restart instructions on the supplied surface.

        Operation:
            Draw the validation diagnostic and restart guidance.
        Input:
            screen and stored message; application font cache.
        Output:
            Renders an error screen; returns None.
        """
        screen.fill(s.BG)
        self.game.ui.text(screen, 'Content needs a quick fix', (60, 70), 48, s.ACCENT)
        self.game.ui.paragraph(screen, self.message, (60, 160, 1150, 350), 28)
        self.game.ui.text(screen, 'Fix the JSON file, then restart the game. Close the window to quit.', (60, 620), 28)


class Game:
    """Own session data, artwork, current scene, and the application lifetime.

    Operation:
        Coordinate the session, display, scene dispatch, and application lifetime.
    Input:
        Pygame events, elapsed seconds, configured content and asset paths.
    Output:
        Owns the active game window and mutable session/scene state.
    """

    def __init__(self):
        """Initialize display-dependent artwork before constructing the session.

        Operation:
            Initialize display-dependent assets before validating the playable session.
        Input:
            Settings paths, source artwork, and JSON content; existing asset loaders.
        Output:
            Creates window/UI/session/court. ContentError creates ErrorScene; unrelated
            startup errors propagate.
        """
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((s.WIDTH, s.HEIGHT))
        pygame.display.set_caption('Food Court')
        self.tomato = Tomato()
        self.scene_assets = SceneAssets()
        self.running = True
        self.ui = UI()

        try:
            self.bank = QuestionBank(s.ROOT / 'data')
            self.session = Session(self.bank)
            from scenes.court import Court
            self.scene = Court(self)
        except ContentError as error:
            self.scene = ErrorScene(self, str(error))

    def restart(self):
        """Reset the session and replace the court, suppressing carried-over clicks.

        Operation:
            Reset session state and replace the court while suppressing carried-over
            clicks.
        Input:
            Current session, content bank, and application.
        Output:
            Creates a fresh Court with its transition guard set; returns None.
        """
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
