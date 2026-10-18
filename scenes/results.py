"""Present final counters and route restart or quit clicks.

Operation:
    Render final totals and route replay/quit input.
Input:
    Completed application/session, cached artwork, and Pygame events.
Output:
    Results frames and restart/quit actions; no persistent score writes.
"""
import pygame
import settings as s
from scenes.base import Scene
from ui.widgets import clicked


class Results(Scene):
    """Display final counters and expose only replay and quit controls.

    Operation:
        Present the final session and only replay/quit controls.
    Input:
        Application with completed session and cached artwork.
    Output:
        Provides result-scene event and draw hooks.
    """

    again=(490,555,300,56)
    quit=(540,630,200,44)

    def __init__(self,game):
        """Retain the application whose final session supplies the counters.

        Operation:
            Bind the completed application for its final totals.
        Input:
            game: current application.
        Output:
            Stores the application reference; returns None.
        """
        self.game=game

    def handle_event(self,event):
        """Restart on replay or stop the application on a quit click.

        Operation:
            Route clicks to replay or quit using the existing rectangles.
        Input:
            event and application state.
        Output:
            Restarts the game or clears running; returns None.
        """
        if clicked(event,self.again):self.game.restart()
        elif clicked(event,self.quit):self.game.running=False

    def draw(self,screen):
        """Draw the dimmed courtroom, final Tomato portrait, and session totals.

        Operation:
            Composite the dimmed court, final portrait, totals, and controls.
        Input:
            screen; session score/counters, cached artwork and UI.
        Output:
            Renders results with existing placement and colors; returns None.
        """
        # Operation: Reuse courtroom artwork under the existing dimming layer and
        #     summary panel.
        # Input: Cached background and final session totals.
        # Output: Existing dimmed courtroom underneath the summary panel.
        screen.blit(self.game.scene_assets.background,(0,0))
        shade=pygame.Surface((s.WIDTH,s.HEIGHT),pygame.SRCALPHA);shade.fill((39,23,15,165));screen.blit(shade,(0,0))
        panel=pygame.Rect(310,100,660,425)
        pygame.draw.rect(screen,'#fff2d5',panel,border_radius=22)
        pygame.draw.rect(screen,'#bf965b',panel,3,border_radius=22)
        ui,session=self.game.ui,self.game.session
        ui.centered_text(screen,"YOU'VE BEEN COOKED!",(640,147),48,'#68402a')
        self.game.scene_assets.tomato.draw(screen,3,(640,315),118)
        ui.centered_text(screen,f'Score: {session.score}',(640,354),48,'#49301f')
        for x,label,key in ((430,'CORRECT','correct'),(640,'INCORRECT','incorrect'),(850,'TIMEOUTS','timeout')):
            ui.centered_text(screen,label,(x,415),24,'#866444')
            ui.centered_text(screen,str(session.counts[key]),(x,451),40,'#49301f')
        ui.button(screen,self.again,'Play Again',color='#795034')
        ui.button(screen,self.quit,'Quit',color='#593f30')
