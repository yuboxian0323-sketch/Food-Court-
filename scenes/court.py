"""Courtroom presentation: source artwork, board transitions, and result ribbons."""
import math
import pygame
import settings as s
from scenes.base import Scene
from ui.widgets import clicked
from ui.target_renderer import TargetRenderer


def ease_out(t):
    return 1-(1-max(0,min(1,t)))**3


class Court(Scene):
    action=s.ACTION
    ink='#49301f'

    def __init__(self, game):
        self.game=game
        self.session=game.session
        self.transitioned=False
        self.target_renderer=TargetRenderer(game.ui)
        self.board_layer=pygame.Surface((s.WIDTH,s.HEIGHT),pygame.SRCALPHA)
        self.banner_cache={}

    def handle_event(self,event):
        if self.transitioned:return
        session=self.session
        if session.stage=='ANSWERING' and event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for target in session.targets:
                if target.contains(event.pos):
                    session.answer(target.fallacy_id)
                    self.transitioned=True
                    return
        if clicked(event,self.action):
            if session.stage=='READING':
                if session.new_fallacies:session.acknowledge_unlock()
                else:session.ready()
                self.transitioned=True
            elif session.stage=='FEEDBACK':
                session.continue_round()
                self.transitioned=True

    def update(self,dt):
        self.session.update(0 if self.transitioned else dt)
        self.transitioned=False
        if self.session.stage=='GAME_OVER':
            from scenes.results import Results
            self.game.scene=Results(self.game)

    def panel(self,screen,rect,fill=(255,247,226,245),border='#c5a16a'):
        rect=pygame.Rect(rect)
        surface=pygame.Surface(rect.size,pygame.SRCALPHA)
        pygame.draw.rect(surface,fill,surface.get_rect(),border_radius=14)
        pygame.draw.rect(surface,border,surface.get_rect(),2,border_radius=14)
        screen.blit(surface,rect)

    def button(self,screen,text):
        rect=pygame.Rect(self.action)
        hover=rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen,'#42291b',rect.move(0,4),border_radius=12)
        self.panel(screen,rect,(255,226,165,255) if hover else (245,204,132,255),'#744923')
        image=self.game.ui.fonts[28].render(text,True,self.ink)
        screen.blit(image,image.get_rect(center=rect.center))

    def draw_hud(self,screen):
        ui,session=self.game.ui,self.session
        self.panel(screen,s.HUD,(51,30,19,225),'#a47846')
        ui.text(screen,f'SCORE  {session.score}',(48,28),26,s.TEXT)
        ui.text(screen,f'ROUND  {session.number}',(730,28),26,s.TEXT)
        pygame.draw.rect(screen,'#412c22',(315,29,280,20),border_radius=7)
        if session.hp:
            pygame.draw.rect(screen,'#89b780' if session.hp>40 else '#dc9371',(315,29,round(280*session.hp/100),20),border_radius=7)
        ui.text(screen,f'HP  {session.hp}/100',(610,28),24,s.TEXT)
        timer=f'{session.remaining:04.1f}s' if session.stage=='ANSWERING' else '--'
        ui.text(screen,f'TIME  {timer}',(930,28),26,'#ffb29a' if session.stage=='ANSWERING' and session.remaining<3 else s.TEXT)
        if session.stage=='ANSWERING':
            pygame.draw.rect(screen,'#e9bf77',(933,52,round(145*session.remaining/s.ANSWER_TIME),3),border_radius=2)
        ui.text(screen,f'{len(session.unlocked)}/18',(1154,29),24,s.ACCENT)

    def draw_dialogue(self,screen):
        ui,session=self.game.ui,self.session
        self.panel(screen,s.DIALOGUE)
        title='KNIFE\'S ARGUMENT'
        text=session.question.argument
        color=self.ink
        size=28
        if session.new_fallacies:
            entry=self.game.bank.fallacies[session.new_fallacies[0]]
            title='NEW FALLACY  /  '+entry['name']
            text=entry['definition']+'\nExample: '+entry['example']
            size=24
        elif session.stage=='FEEDBACK':
            name=self.game.bank.fallacies[session.question.fallacy]['name']
            result={'correct':'CORRECT!  +100 POINTS','incorrect':'INCORRECT  -20 HP','timeout':'TIME\'S UP  -20 HP'}[session.result]
            title=result+'   /   '+name
            text=session.question.explanation
            color='#356341' if session.result=='correct' else '#9e372b'
        elif session.stage=='OBJECTION_ANIMATION':title='CHEF: OBJECTION SUSTAINED!'
        elif session.stage=='MISTAKE_ANIMATION':title='THE CHEF IS RULING...'
        ui.text(screen,title,(122,94),24,color)
        ui.paragraph(screen,text,(122,124,1036,68),size,self.ink)

    def draw_board(self,screen):
        session=self.session
        if session.stage in ('READING','GAME_OVER'):return
        progress=max(0,min(1,session.board_progress))
        if session.stage=='BOARD_ENTER':
            eased=ease_out(progress)
            offset=round(s.BOARD_SLIDE_DISTANCE*(1-eased))
            alpha=round(255*eased)
        elif session.stage=='BOARD_EXIT':
            offset=round(s.BOARD_SLIDE_DISTANCE*(1-progress)**2)
            alpha=round(255*progress)
        else:offset=0;alpha=255
        layer=self.board_layer
        layer.fill((0,0,0,0))
        assets=self.game.scene_assets
        x,y,_,_=s.BOARD_RECT
        layer.blit(assets.board_shadow,(x-16,y-6))
        layer.blit(assets.board,(x,y))
        if session.stage!='BOARD_ENTER':
            for target in session.targets:
                self.target_renderer.draw(layer,target,len(session.targets),session.stage)
        layer.set_alpha(alpha)
        screen.blit(layer,(0,offset))

    def draw_objection(self,screen):
        progress=ease_out(self.session.objection_progress)
        x=round(s.TOMATO_ANCHOR[0]+(s.KNIFE_ANCHOR[0]-s.TOMATO_ANCHOR[0])*progress)
        y=round(460+70*progress-80*math.sin(progress*math.pi))
        image=self.game.ui.fonts[80].render('OBJECTION!',True,'#fff3ca')
        outline=self.game.ui.fonts[80].render('OBJECTION!',True,'#65401e')
        rect=image.get_rect(center=(x,y))
        pygame.draw.line(screen,'#edbd58',(x+100,y+42),(x-100,y+42),4)
        pygame.draw.polygon(screen,'#edbd58',[(x-115,y+42),(x-93,y+30),(x-93,y+54)])
        for dx,dy in ((-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,2)):
            screen.blit(outline,rect.move(dx,dy))
        screen.blit(image,rect)

    def banner(self,text):
        if text not in self.banner_cache:
            width,height=s.WIDTH+48,s.BANNER_HEIGHT
            image=pygame.Surface((width,height+14),pygame.SRCALPHA)
            pygame.draw.polygon(image,(39,12,9,100),[(0,12),(width,height//2+12),(width,height+12),(0,height+12)])
            pygame.draw.polygon(image,'#a42f2a',[(0,0),(width,0),(width-20,height//2),(width,height),(0,height),(20,height//2)])
            pygame.draw.rect(image,'#bd4034',(20,9,width-40,height-18))
            pygame.draw.line(image,'#ed8d6a',(24,12),(width-24,12),2)
            pygame.draw.line(image,'#79271f',(24,height-10),(width-24,height-10),3)
            for x in (75,105,width-125,width-95):
                pygame.draw.polygon(image,'#da6553',[(x,28),(x+10,28),(x-14,height-28),(x-24,height-28)])
            lettering=self.game.ui.fonts[96].render(text,True,'#fff6e5')
            image.blit(lettering,lettering.get_rect(center=(width//2,height//2)))
            self.banner_cache[text]=image
        return self.banner_cache[text]

    def draw_wrong_banner(self,screen):
        session=self.session
        text=s.TIMEOUT_BANNER_TEXT if session.result=='timeout' else s.WRONG_BANNER_TEXT
        image=self.banner(text)
        elapsed=session.banner_elapsed
        if elapsed<s.BANNER_IN_DURATION:
            t=elapsed/s.BANNER_IN_DURATION
            # A very small ease-out-back settling, not a screen shake.
            u=t-1;settle=1+1.18*u**3+.18*u**2
            x=-image.get_width()+(image.get_width()-24)*settle
        elif elapsed<s.BANNER_IN_DURATION+s.BANNER_HOLD_DURATION:x=-24
        else:
            t=(elapsed-s.BANNER_IN_DURATION-s.BANNER_HOLD_DURATION)/s.BANNER_OUT_DURATION
            x=-24+(s.WIDTH+24)*t*t*t
        screen.blit(image,(round(x),s.BANNER_CENTER_Y-s.BANNER_HEIGHT//2))

    def draw(self,screen):
        session=self.session
        self.game.scene_assets.draw_courtroom(screen,session)
        self.draw_board(screen)
        self.draw_hud(screen)
        self.draw_dialogue(screen)
        if session.stage=='READING':
            size=20 if len(session.targets)>3 else 24
            for target in session.targets:
                for hover in (False,True):self.target_renderer.sprite(target.name,target.width,target.height,size,'',hover)
            self.button(screen,'Got it' if session.new_fallacies else 'Ready')
        elif session.stage=='FEEDBACK':self.button(screen,'View results' if session.game_over else 'Continue')
        if session.tint_alpha:
            tint=pygame.Surface((s.WIDTH,s.HEIGHT),pygame.SRCALPHA)
            tint.fill((198,48,38,session.tint_alpha));screen.blit(tint,(0,0))
        if session.stage=='OBJECTION_ANIMATION':self.draw_objection(screen)
        elif session.stage=='MISTAKE_ANIMATION':self.draw_wrong_banner(screen)
