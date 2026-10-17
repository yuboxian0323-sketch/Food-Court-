import pygame
import settings as s
from scenes.base import Scene
from ui.widgets import clicked


class Results(Scene):
    again=(490,555,300,56)
    quit=(540,630,200,44)

    def __init__(self,game):self.game=game

    def handle_event(self,event):
        if clicked(event,self.again):self.game.restart()
        elif clicked(event,self.quit):self.game.running=False

    def draw(self,screen):
        screen.blit(self.game.scene_assets.background,(0,0))
        shade=pygame.Surface((s.WIDTH,s.HEIGHT),pygame.SRCALPHA);shade.fill((39,23,15,165));screen.blit(shade,(0,0))
        panel=pygame.Rect(310,100,660,425)
        pygame.draw.rect(screen,'#fff2d5',panel,border_radius=22)
        pygame.draw.rect(screen,'#bf965b',panel,3,border_radius=22)
        ui,session=self.game.ui,self.game.session
        title=ui.fonts[48].render("YOU'VE BEEN COOKED!",True,'#68402a')
        screen.blit(title,title.get_rect(center=(640,147)))
        self.game.scene_assets.tomato.draw(screen,3,(640,315),118)
        score=ui.fonts[48].render(f'Score: {session.score}',True,'#49301f')
        screen.blit(score,score.get_rect(center=(640,354)))
        for x,label,key in ((430,'CORRECT','correct'),(640,'INCORRECT','incorrect'),(850,'TIMEOUTS','timeout')):
            text=ui.fonts[24].render(label,True,'#866444');screen.blit(text,text.get_rect(center=(x,415)))
            value=ui.fonts[40].render(str(session.counts[key]),True,'#49301f');screen.blit(value,value.get_rect(center=(x,451)))
        ui.button(screen,self.again,'Play Again',color='#795034')
        ui.button(screen,self.quit,'Quit',color='#593f30')
