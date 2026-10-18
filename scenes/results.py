import pygame
import settings as s
from scenes.base import Scene
from ui.widgets import clicked


class Results(Scene):
   
    #Buttons (x,y,width,height)
    again=(490,555,300,56)
    quit=(540,630,200,44)

    def __init__(self,game): #Result screen created
        self.game=game
        self.shade=pygame.Surface((s.WIDTH,s.HEIGHT),pygame.SRCALPHA)
        self.shade.fill((39,23,15,165))

    def handle_event(self,event):
      #Responds to input events; clicks on buttons restart or quit the game.
        if clicked(event,self.again):self.game.restart()
        elif clicked(event,self.quit):self.game.running=False

    def draw(self,screen): #Draw background 



        #Draws cached courtroom background from top-left (0,0)
        screen.blit(self.game.scene_assets.background,(0,0))

        #Dims background
        screen.blit(self.shade,(0,0))

        #Draw results panel and text
        panel=pygame.Rect(310,100,660,425)
        pygame.draw.rect(screen,'#fff2d5',panel,border_radius=22)
        pygame.draw.rect(screen,'#bf965b',panel,3,border_radius=22)

        #Get UI and session objects
        ui,session=self.game.ui,self.game.session

        #Display title
        ui.centered_text(screen,"YOU'VE BEEN COOKED!",(640,147),48,'#68402a')

        #Display tomato
        self.game.scene_assets.tomato.draw(
                screen,
                hp=session.hp,
                anchor=(640, 315),
                width=118,
            )

        #Final score 
        ui.centered_text(screen,f'Score: {session.score}',(640,354),48,'#49301f')

        #Statistics
        for x,label,key in ((430,'CORRECT','correct'),(640,'INCORRECT','incorrect'),(850,'TIMEOUTS','timeout')):
            ui.centered_text(screen,label,(x,415),24,'#866444')
            ui.centered_text(screen,str(session.counts[key]),(x,451),40,'#49301f')
        ui.button(screen,self.again,'Play Again',color='#795034')
        ui.button(screen,self.quit,'Quit',color='#593f30')
