"""Load inspected source artwork without altering it on disk."""
from functools import lru_cache
import math
import pygame
import settings as s
from entities.character import _draw_chef


class SpriteStrip:
    def __init__(self, path):
        self.frames=[]
        try:
            sheet=pygame.image.load(str(path)).convert_alpha()
            # Both supplied strips paint five frames in the first 5586 pixels;
            # the remaining 5678 columns are transparent, not more frames.
            cells=[]
            for i in range(5):
                left,right=round(i*5586/5),round((i+1)*5586/5)
                cells.append(sheet.subsurface((left,0,right-left,sheet.get_height())).copy())
            top=min(frame.get_bounding_rect().top for frame in cells)
            bottom=max(frame.get_bounding_rect().bottom for frame in cells)
            width=max(frame.get_width() for frame in cells)
            for cell in cells:
                # A common canvas keeps every expression's feet/handle aligned.
                frame=pygame.Surface((width,bottom-top),pygame.SRCALPHA)
                frame.blit(cell,(0,-top))
                self.frames.append(frame)
        except (pygame.error,OSError,ValueError):
            pass

    @lru_cache(maxsize=30)
    def scaled(self, index, width):
        if not self.frames:return None
        frame=self.frames[index]
        return pygame.transform.smoothscale(frame,(width,round(width*frame.get_height()/frame.get_width())))

    def draw(self, screen, index, anchor, width):
        frame=self.scaled(index,width)
        if frame is not None:screen.blit(frame,frame.get_rect(midbottom=anchor))


class SceneAssets:
    # Actual faces: closed/confident, smirk, open mouth, angry open mouth + vein,
    # red-tinted anger. No separate surprised Knife face is present.
    KNIFE_EXPRESSIONS={'talking':2,'waiting':0,'shocked':3,'smug':1}

    def __init__(self):
        self.knife=SpriteStrip(s.KNIFE_ASSET)
        self.tomato=SpriteStrip(s.ROOT/'assets/Tomato_SpriteSheet.png')
        self.background=self.load_background()
        self.board=self.load_board()
        self.chef_frames={state:self.make_chef(state) for state in ('listening','surprised','stern')}
        self.board_shadow=self.make_shadow((s.BOARD_RECT[2],s.BOARD_RECT[3]))

    def load_background(self):
        try:
            source=pygame.image.load(str(s.COURTROOM_ASSET)).convert()
            scale=max(s.WIDTH/source.get_width(),s.HEIGHT/source.get_height())
            image=pygame.transform.smoothscale(source,(round(source.get_width()*scale),round(source.get_height()*scale)))
            result=pygame.Surface((s.WIDTH,s.HEIGHT))
            result.blit(image,image.get_rect(center=(s.WIDTH//2,s.HEIGHT//2)))
            return result
        except (pygame.error,OSError):
            result=pygame.Surface((s.WIDTH,s.HEIGHT));result.fill('#a87c50')
            pygame.draw.rect(result,'#63402e',s.CENTRAL_BENCH_FOREGROUND)
            return result

    def load_board(self):
        try:
            image=pygame.image.load(str(s.BOARD_ASSET)).convert_alpha()
            # This inspected JPEG has a white exterior and white handle hole,
            # and no white painted details on the board. This operation is only
            # for the board; character eyes/highlights retain source alpha.
            white=pygame.mask.from_threshold(image,(255,255,255,255),(65,65,65,255))
            alpha=white.to_surface(setcolor=(255,255,255,0),unsetcolor=(255,255,255,255))
            image.blit(alpha,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
            image=image.subsurface(image.get_bounding_rect()).copy()
            image=pygame.transform.rotate(image,-90)
            width=s.BOARD_RECT[2]
            height=round(width*image.get_height()/image.get_width())
            return pygame.transform.smoothscale(image,(width,height))
        except (pygame.error,OSError,ValueError):
            image=pygame.Surface(s.BOARD_RECT[2:],pygame.SRCALPHA)
            pygame.draw.rect(image,'#925f2e',image.get_rect(),border_radius=42)
            pygame.draw.rect(image,'#c69854',image.get_rect().inflate(-18,-18),border_radius=36)
            for y in range(30,image.get_height()-20,32):
                pygame.draw.line(image,'#bd8c45',(40,y),(image.get_width()-40,y+5),2)
            return image

    @staticmethod
    def make_shadow(size):
        shadow=pygame.Surface((size[0]+32,size[1]+32),pygame.SRCALPHA)
        for inset in range(16,0,-2):
            pygame.draw.rect(shadow,(25,13,5,3+(16-inset)),(16-inset,16-inset,size[0]+inset*2,size[1]+inset*2),border_radius=50)
        return shadow

    @staticmethod
    def make_chef(expression):
        portrait=pygame.Surface((220,240),pygame.SRCALPHA)
        _draw_chef(portrait,(110,240),expression)
        return pygame.transform.smoothscale(portrait,s.CHEF_PORTRAIT_SIZE)

    def draw_courtroom(self, screen, session):
        screen.blit(self.background,(0,0))
        chef=self.chef_frames[session.chef_expression]
        screen.blit(chef,chef.get_rect(midbottom=s.CHEF_ANCHOR))
        # Reuse precisely the same transformed background pixels. The Chef is
        # drawn first, then the physical bench front occludes their lower body.
        bench=pygame.Rect(s.CENTRAL_BENCH_FOREGROUND)
        screen.blit(self.background,bench,bench)
        for anchor,width in ((s.KNIFE_ANCHOR,350),(s.TOMATO_ANCHOR,180)):
            shadow=pygame.Surface((width,20),pygame.SRCALPHA)
            pygame.draw.ellipse(shadow,(32,15,6,55),(0,0,width,20))
            screen.blit(shadow,(anchor[0]-width//2,anchor[1]-14))
        if self.knife.frames:
            self.knife.draw(screen,self.KNIFE_EXPRESSIONS[session.gadget_expression],s.KNIFE_ANCHOR,s.KNIFE_WIDTH)
        else:
            pygame.draw.polygon(screen,'#b7b9b5',[(90,590),(265,590),(290,540),(110,540)])
        if self.tomato.frames:
            index=4 if session.stage=='MISTAKE_ANIMATION' else {
                'normal':0,'nervous':2,'panic':3
            }[session.tomato_expression]
            anchor=s.TOMATO_ANCHOR
            if session.stage=='MISTAKE_ANIMATION':
                elapsed=session.banner_elapsed
                decay=max(0,1-elapsed/session.banner_duration)
                shake_x=round(math.sin(elapsed*48)*7*decay)
                shake_y=round((math.cos(elapsed*48)-1)*2*decay)
                anchor=(anchor[0]+shake_x,anchor[1]+shake_y)
            self.tomato.draw(screen,index,anchor,s.TOMATO_WIDTH)
        else:
            pygame.draw.circle(screen,'#c64f35',(s.TOMATO_ANCHOR[0],s.TOMATO_ANCHOR[1]-90),90)
        desk=pygame.Rect(s.FRONT_DESK_FOREGROUND)
        screen.blit(self.background,desk,desk)
