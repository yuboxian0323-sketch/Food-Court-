import math
import pygame
import settings as s
from entities.character import draw_chef, draw_gadget
from scenes.base import Scene
from ui.widgets import clicked
from ui.target_renderer import TargetRenderer


class Court(Scene):
    action = s.ACTION
    ink = '#23384d'

    def __init__(self, game):
        self.game = game
        self.session = game.session
        self.transitioned = False
        self.target_renderer = TargetRenderer(game.ui)

    def handle_event(self, event):
        if self.transitioned:
            return
        session = self.session
        if session.stage == 'ANSWERING' and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in session.targets:
                if target.contains(event.pos):
                    session.answer(target.fallacy_id)
                    self.transitioned = True
                    return
        if clicked(event, self.action):
            if session.stage == 'READING':
                if session.new_fallacies:
                    session.acknowledge_unlock()
                else:
                    session.ready()
                self.transitioned = True
            elif session.stage == 'FEEDBACK':
                if session.game_over:
                    from scenes.results import Results
                    self.game.scene = Results(self.game)
                else:
                    session.next_round()
                self.transitioned = True

    def update(self, dt):
        # Don't consume time before the new stage has been displayed once.
        self.session.update(0 if self.transitioned else dt)
        self.transitioned = False

    def box(self, screen, rect, fill, border='#a3b1b9', radius=8):
        pygame.draw.rect(screen, fill, rect, border_radius=radius)
        pygame.draw.rect(screen, border, rect, 1, border_radius=radius)

    def label(self, screen, text, rect, fill='#ffffff', enabled=False):
        rect = pygame.Rect(rect)
        hover = enabled and rect.collidepoint(pygame.mouse.get_pos())
        self.box(screen, rect, '#fff0c7' if hover else fill, self.ink)
        image = self.game.ui.fonts[26].render(text, True, self.ink)
        screen.blit(image, image.get_rect(center=rect.center))

    def draw_target(self, screen, target):
        self.target_renderer.draw(screen,target,len(self.session.targets),self.session.stage)

    def draw_objection(self, screen):
        progress = self.session.objection_progress
        x = int(350 + (s.GADGET_ANCHOR[0]-350)*progress)
        y = 148 - int(16*math.sin(progress*math.pi))
        pygame.draw.line(screen, '#bd4e35', (350, 177), (s.GADGET_ANCHOR[0], 177), 5)
        pygame.draw.polygon(screen, '#bd4e35', [(640,177),(621,166),(621,188)])
        image = self.game.ui.fonts[64].render('OBJECTION!', True, '#fff2cf')
        outline = self.game.ui.fonts[64].render('OBJECTION!', True, '#8b352c')
        rect = image.get_rect(center=(x, y))
        for dx, dy in ((-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,2)):
            screen.blit(outline, rect.move(dx,dy))
        screen.blit(image, rect)

    def draw(self, screen):
        ui, session = self.game.ui, self.session
        screen.fill('#faf7f0')
        pygame.draw.rect(screen, '#203854', s.HUD)
        ui.text(screen, f'Score: {session.score}', (20, 16), 32)
        self.box(screen, (260, 15, 320, 30), '#172b40', radius=4)
        if session.hp:
            pygame.draw.rect(screen, '#50b887' if session.hp > 40 else '#ed9a82', (260,15,int(320*session.hp/100),30), border_radius=4)
        ui.text(screen, f'HP {session.hp}/100', (270,18), 26)
        ui.text(screen, f'Question {session.number}', (600,16), 28)
        timer = str(math.ceil(session.remaining)) if session.stage == 'ANSWERING' else '--'
        ui.text(screen, f'Time: {timer}', (820,12), 28, s.RED if session.stage == 'ANSWERING' and session.remaining < 3 else s.TEXT)
        if session.stage == 'ANSWERING':
            pygame.draw.rect(screen, s.ACCENT, (820,43,int(220*session.remaining/s.ANSWER_TIME),4))
        ui.text(screen, f'{len(session.unlocked)}/18 fallacies', (1090,20), 24, s.ACCENT)

        self.box(screen, s.CHARACTER_AREA, '#e8f0f9')
        self.game.tomato.draw(screen, session.hp, position=(289,109), scale=.55)
        draw_chef(screen, s.CHEF_ANCHOR, session.chef_expression)
        draw_gadget(screen, s.GADGET_ANCHOR, session.gadget_expression)
        ui.text(screen, 'Tomato / defendant', (252,79), 24, self.ink)
        ui.text(screen, 'Gadget / opponent', (548,79), 24, self.ink)
        ui.text(screen, 'Chef / judge', (866,79), 24, self.ink)
        state = {'listening':'Listening', 'surprised':'Objection sustained!', 'stern':'Objection missed'}[session.chef_expression]
        ui.text(screen, state, (1010,120), 20, self.ink)

        self.box(screen, s.DIALOGUE, '#ffffff', self.ink)
        text = session.question.argument
        title = 'Gadget testimony - read, then press Ready'
        title_color = self.ink
        if session.new_fallacies:
            metadata = self.game.bank.fallacies[session.new_fallacies[0]]
            title = 'New fallacy unlocked!  ' + metadata['name']
            text = metadata['definition'] + '\nExample: ' + metadata['example']
        elif session.stage == 'FEEDBACK':
            name = self.game.bank.fallacies[session.question.fallacy]['name']
            outcome = {'correct':'Correct! +100', 'incorrect':'Incorrect. -20 HP', 'timeout':'Too late. -20 HP'}[session.result]
            title = f'{outcome}  |  Correct fallacy: {name}'
            text = session.question.explanation
            title_color = '#28704c' if session.result == 'correct' else '#9b3931'
        elif session.stage == 'ANSWERING':
            title = 'Gadget testimony - click the moving fallacy label'
        elif session.stage == 'OBJECTION_ANIMATION':
            title = 'Chef: Objection sustained!'
        ui.text(screen, title, (156,239), 24, title_color)
        ui.paragraph(screen, text, (156,258 if session.new_fallacies else 264,968,72 if session.new_fallacies else 64), 24 if session.new_fallacies else 28, self.ink)

        self.box(screen, s.LABEL_REGION, '#edf5ed')
        if session.stage != 'READING':
            for target in session.targets:
                self.draw_target(screen, target)
        else:
            # Warm the two appearance sprites during untimed reading so their
            # first rasterization cannot stall the first moving frame.
            size=20 if len(session.targets)>3 else 24
            for target in session.targets:
                for hover in (False,True):
                    self.target_renderer.sprite(target.name,target.width,target.height,size,'',hover)
            ui.text(screen, 'Read at your own pace. Your 10 seconds start after Ready.', (160,475), 28, self.ink)
        if session.stage in ('READING', 'FEEDBACK'):
            label = ('Got it' if session.new_fallacies else 'Ready') if session.stage == 'READING' else 'View results' if session.game_over else 'Continue'
            self.label(screen, label, self.action, '#ffe2a3', True)
        if session.stage == 'OBJECTION_ANIMATION':
            self.draw_objection(screen)
        if session.tint_alpha:
            tint = pygame.Surface((s.WIDTH,s.HEIGHT), pygame.SRCALPHA)
            tint.fill((220,60,55,session.tint_alpha))
            screen.blit(tint,(0,0))
