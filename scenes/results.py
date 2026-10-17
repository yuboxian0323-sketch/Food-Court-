import settings as s
from scenes.base import Scene
from ui.widgets import clicked


class Results(Scene):
    again = (490, 550, 300, 58)
    quit = (490, 625, 300, 48)

    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        if clicked(event, self.again):
            self.game.restart()
        elif clicked(event, self.quit):
            self.game.running = False

    def draw(self, screen):
        screen.fill(s.BG)
        ui, session = self.game.ui, self.game.session
        ui.panel(screen, (220, 80, 840, 440))
        ui.text(screen, "YOU'VE BEEN COOKED!", (355, 112), 48, s.ACCENT)
        self.game.tomato.draw(screen, 0, position=(240, 220))
        ui.text(screen, f'Final score: {session.score}', (480, 205), 40)
        for i, (label, value) in enumerate(session.counts.items()):
            ui.text(screen, f'{label.title()}: {value}', (480, 275+i*45), 32, s.MUTED)
        ui.text(screen, f'Rounds played: {session.number}', (480, 425), 28)
        ui.button(screen, self.again, 'Play Again')
        ui.button(screen, self.quit, 'Quit')
