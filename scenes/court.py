import pygame
import settings as s
from scenes.base import Scene
from ui.widgets import clicked
from ui.target_renderer import TargetRenderer, label_font_size


def ease_out(t):
    """Return cubic ease-out progress with its input clamped to zero through one.

    Operation:
        Clamp progress and apply cubic ease-out.
    Input:
        t: normalized progress.
    Output:
        Returns a float in [0, 1] without state changes.
    """
    return 1-(1-max(0,min(1,t)))**3


class Court(Scene):
    """Compose the courtroom and route input according to explicit round stages.

    Operation:
        Compose the courtroom and route controls through explicit round stages.
    Input:
        Application, current Session, UI, and cached artwork.
    Output:
        Owns reusable rendering surfaces and a per-event-batch transition guard.
    """

    action=s.ACTION
    ink='#49301f'

    def __init__(self, game):
        """Bind the current session and allocate reusable board/banner surfaces.

        Operation:
            Bind the session and allocate reusable board and banner resources.
        Input:
            game: initialized application with UI and Session.
        Output:
            Creates renderer/layers/cache and clears the transition guard; returns None.
        """
        self.game=game
        self.session=game.session
        self.transitioned=False
        self.target_renderer=TargetRenderer(game.ui)
        self.board_layer=pygame.Surface((s.WIDTH,s.HEIGHT),pygame.SRCALPHA)
        self.mistake_tint=pygame.Surface((s.WIDTH,s.HEIGHT),pygame.SRCALPHA)
        self.panel_cache={}
        self.banner_cache={}

    def handle_event(self,event):
        """Handle visible controls and the first valid answer in an event batch.

        Operation:
            Accept only visible controls and the first valid answer in an event batch.
        Input:
            event: Pygame input; session stage; displayed target positions; action
            rectangle.
        Output:
            May start/resolve/dismiss a round or acknowledge an unlock; locks later
            events after a transition; returns None.
        """
        if self.transitioned:return
        session=self.session
        if session.stage=='ANSWERING' and event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            for target in session.targets:
                if target.contains(event.pos):
                    session.answer(target.fallacy_id)
                    self.transitioned=True
                    return
        # Operation: Transition stages expose no actionable controls; the event cannot
        #     pass through.
        # Input: Event, action rectangle, stage, and transition guard.
        # Output: Only READING/FEEDBACK controls can transition; hidden choices receive
        #     no clicks.
        if clicked(event,self.action):
            if session.stage=='READING':
                if session.new_fallacies:session.acknowledge_unlock()
                else:session.ready()
                self.transitioned=True
            elif session.stage=='FEEDBACK':
                session.continue_round()
                self.transitioned=True

    def update(self,dt):
        """Advance the session in seconds, preserving the first transition frame.

        Operation:
            Advance the current stage unless input already transitioned this frame.
        Input:
            dt: seconds; transitioned flag and session state.
        Output:
            Updates session, clears the guard, and switches to Results only after
            GAME_OVER; returns None.
        """
        self.session.update(0 if self.transitioned else dt)
        self.game.scene_assets.update_chef(dt,self.session.chef_expression)
        self.transitioned=False
        if self.session.stage=='GAME_OVER':
            from scenes.results import Results
            self.game.scene=Results(self.game)

    def panel(self,screen,rect,fill=(255,247,226,245),border='#c5a16a'):
        """Draw a rounded translucent panel in scene-pixel rect coordinates.

        Operation:
            Draw a bordered rounded alpha panel at the supplied rectangle.
        Input:
            screen, rect: scene pixels, fill: RGBA, border: color.
        Output:
            Blits the panel; returns None.
        """
        rect=pygame.Rect(rect)
        key=(rect.size,fill,border)
        surface=self.panel_cache.get(key)
        if surface is None:
            surface=pygame.Surface(rect.size,pygame.SRCALPHA)
            pygame.draw.rect(surface,fill,surface.get_rect(),border_radius=14)
            pygame.draw.rect(surface,border,surface.get_rect(),2,border_radius=14)
            self.panel_cache[key]=surface
        screen.blit(surface,rect)

    def button(self,screen,text):
        """Draw the court action control; hover changes its appearance only.

        Operation:
            Draw the existing action button with cosmetic hover highlighting.
        Input:
            screen, text, self.action, mouse position, and cached UI fonts.
        Output:
            Renders the button and centered text; returns None.
        """
        rect=pygame.Rect(self.action)
        hover=rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen,'#42291b',rect.move(0,4),border_radius=12)
        self.panel(screen,rect,(255,226,165,255) if hover else (245,204,132,255),'#744923')
        self.game.ui.centered_text(screen,text,rect.center,28,self.ink)

    def draw_hud(self,screen):
        """Draw score, HP, round, and timer without changing session state.

        Operation:
            Read session totals and draw the slim HUD without changing them.
        Input:
            screen; score, HP, round, unlocked topics, remaining seconds, and stage.
        Output:
            Renders HUD and active timer bar; returns None.
        """
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
        """Draw the argument, unlock card, ruling, or explanation for the stage.

        Operation:
            Choose argument, unlock card, ruling, or explanation according to stage.
        Input:
            screen; current question, result, unlock state, and UI wrapping.
        Output:
            Renders dialogue in its existing rectangle; returns None.
        """
        ui,session=self.game.ui,self.session
        self.panel(screen,s.DIALOGUE)
        title='KNIFE:' #Speaker title
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
        ui.text(screen,title,(122,564),24,color) #Speaker
        ui.paragraph(screen,text,(122,604,1036,68),size,self.ink) #Dialogue

    def draw_board(self,screen):
        """Composite the board and frozen or moving labels as one animated layer.

        Operation:
            Composite board, shadow, and labels, then apply shared slide/fade.
        Input:
            screen; board progress/stage, targets, cached artwork, and scene-pixel
            placement.
        Output:
            Blits the board layer; entrance hides labels and READING/GAME_OVER skip it;
            returns None.
        """
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
        # Operation: Composite the moving answer labels with their existing
        #     slide/fade transition.
        # Input: Target render state and board progress.
        # Output: One translated/alpha-composited label layer; board artwork remains
        #     hidden.
        layer=self.board_layer
        layer.fill((0,0,0,0))
        for target in session.targets:
            self.target_renderer.draw(layer,target,len(session.targets),session.stage)
        layer.set_alpha(alpha)
        screen.blit(layer,(0,offset))

    def draw_objection(self,screen):
        """Draw the correct-only green ribbon through the shared animation path.

        Operation:
            Delegate the correct effect to the shared green ribbon path.
        Input:
            screen and current banner elapsed time in the session.
        Output:
            Renders green OBJECTION! only; returns None.
        """
        self.draw_outcome_banner(screen, 'OBJECTION!', '#28784b')

    def banner(self,text,background='#bd4034'):
        """Return a cached ribbon configured by message and background color.

        Operation:
            Build/cache shared ribbon geometry with a message and color palette.
        Input:
            text, background color; configured width/height and cached UI fonts.
        Output:
            Returns a Surface and may populate banner_cache. Default red retains
            text-only keys; colored variants use distinct keys.
        """
        # Operation: Share geometry and typography while preserving the red palette byte
        #     for byte.
        # Input: Message/background key, font cache, and existing ribbon dimensions.
        # Output: Cached geometry/lettering with unchanged red pixels and distinct green
        #     variants.
        key=text if background=='#bd4034' else (text,background)
        if key not in self.banner_cache:
            width,height=s.WIDTH+48,s.BANNER_HEIGHT
            image=pygame.Surface((width,height+14),pygame.SRCALPHA)
            pygame.draw.polygon(image,(39,12,9,100),[(0,12),(width,height//2+12),(width,height+12),(0,height+12)])
            edge,highlight,shade,accent = (
                ('#a42f2a','#ed8d6a','#79271f','#da6553')
                if background=='#bd4034' else
                ('#1e603b','#86be91','#174d30','#4e9968')
            )
            pygame.draw.polygon(image,edge,[(0,0),(width,0),(width-20,height//2),(width,height),(0,height),(20,height//2)])
            pygame.draw.rect(image,background,(20,9,width-40,height-18))
            pygame.draw.line(image,highlight,(24,12),(width-24,12),2)
            pygame.draw.line(image,shade,(24,height-10),(width-24,height-10),3)
            for x in (75,105,width-125,width-95):
                pygame.draw.polygon(image,accent,[(x,28),(x+10,28),(x-14,height-28),(x-24,height-28)])
            self.game.ui.centered_text(image,text,(width//2,height//2),96,'#fff6e5')
            self.banner_cache[key]=image
        return self.banner_cache[key]

    def draw_wrong_banner(self,screen):
        """Draw the red wrong-answer or timeout ribbon with configured wording.

        Operation:
            Select the configured wrong or timeout text for the red ribbon.
        Input:
            screen; session.result and configured mistake messages.
        Output:
            Delegates one red ribbon draw; returns None.
        """
        session=self.session
        text=s.TIMEOUT_BANNER_TEXT if session.result=='timeout' else s.WRONG_BANNER_TEXT
        self.draw_outcome_banner(screen,text)

    def draw_outcome_banner(self,screen,text,background='#bd4034'):
        """Draw one ribbon through shared entrance, hold, and exit phases.

        Operation:
            Place the ribbon through the unchanged entrance, hold, and exit equations.
        Input:
            screen, text, background; session.banner_elapsed and phase durations in
            seconds.
        Output:
            Blits one animated ribbon at scene-pixel coordinates; does not resolve
            outcomes or advance time; returns None.
        """
        image=self.banner(text,background)
        elapsed=self.session.banner_elapsed
        # Operation: These phase equations are the original red animation, shared by
        #     both colors.
        # Input: Elapsed seconds and configured entrance/hold/exit durations.
        # Output: Shared screen x offset for both ribbon colors.
        if elapsed<s.BANNER_IN_DURATION:
            t=elapsed/s.BANNER_IN_DURATION
            # Operation: A very small ease-out-back settling, not a screen shake.
            # Input: Normalized entrance time and existing ease-out-back coefficients.
            # Output: Small entrance settling offset without screen shake.
            u=t-1;settle=1+1.18*u**3+.18*u**2
            x=-image.get_width()+(image.get_width()-24)*settle
        elif elapsed<s.BANNER_IN_DURATION+s.BANNER_HOLD_DURATION:x=-24
        else:
            t=(elapsed-s.BANNER_IN_DURATION-s.BANNER_HOLD_DURATION)/s.BANNER_OUT_DURATION
            x=-24+(s.WIDTH+24)*t*t*t
        screen.blit(image,(round(x),s.BANNER_CENTER_Y-s.BANNER_HEIGHT//2))

    def draw(self,screen):
        """Composite court, board, UI, tint, and exactly one outcome effect in order.

        Operation:
            Draw court, board, HUD/dialogue, controls, tint, then one outcome effect.
        Input:
            screen; current session stage, artwork, target state, and UI.
        Output:
            Renders the current frame and may warm rendering caches; returns None.
        """
        session=self.session
        self.game.scene_assets.draw_courtroom(screen,session)
        self.draw_board(screen)
        self.draw_hud(screen)
        self.draw_dialogue(screen)
        if session.stage=='READING':
            size=label_font_size(len(session.targets))
            for target in session.targets:
                for hover in (False,True):self.target_renderer.sprite(target.name,target.width,target.height,size,'',hover)
            self.button(screen,'Got it' if session.new_fallacies else 'Ready')
        elif session.stage=='FEEDBACK':self.button(screen,'View results' if session.game_over else 'Continue')
        # Operation: Keep the existing tint below the outcome ribbon and above the
        #     courtroom.
        # Input: Mistake tint alpha, stage, and rendered court/UI layers.
        # Output: Tint overlays the court; exactly one outcome ribbon is drawn above it.
        if session.tint_alpha:
            self.mistake_tint.fill((198,48,38,session.tint_alpha))
            screen.blit(self.mistake_tint,(0,0))
        if session.stage=='OBJECTION_ANIMATION':self.draw_objection(screen)
        elif session.stage=='MISTAKE_ANIMATION':self.draw_wrong_banner(screen)
