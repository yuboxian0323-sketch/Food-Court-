"""Load inspected source artwork without altering it on disk.

Operation:
    Extract/cache source artwork and compose actors with aligned occlusion.
Input:
    Configured asset paths, initialized display, session reactions, and scene-pixel
    anchors.
Output:
    Runtime surfaces or existing load fallbacks; original source assets are never
    rewritten.
"""
from functools import lru_cache
import math
import pygame
import settings as s
from entities.chef import Chef
from systems.expressions import TOMATO_FRAMES


class SpriteStrip:
    """Extract five aligned expressions from the inspected painted strip region.

    Operation:
        Crop the inspected painted region into five aligned runtime expressions.
    Input:
        Source image path, initialized display, and fixed painted extent.
    Output:
        Owns source-alpha frames and aspect-preserving scaled-frame cache.
    """

    def __init__(self, path):
        """Crop source cells onto a common canvas and preserve load fallbacks.

        Operation:
            Load/crop five painted cells onto common vertical/width bounds.
        Input:
            path and supplied strips with painted content in the first 5586 columns.
        Output:
            Sets frames; caught load/format/crop errors are suppressed; source
            files are unchanged.
        """
        self.frames=[]
        try:
            sheet=pygame.image.load(str(path)).convert_alpha()
            # Operation: Both supplied strips paint five frames in the first 5586
            #     pixels; the remaining 5678 columns are transparent, not more frames.
            # Input: Loaded sheet and inspected 5586-column painted extent.
            # Output: Five runtime cells; the transparent tail is excluded.
            cells=[]
            for i in range(5):
                left,right=round(i*5586/5),round((i+1)*5586/5)
                cells.append(sheet.subsurface((left,0,right-left,sheet.get_height())).copy())
            top=min(frame.get_bounding_rect().top for frame in cells)
            bottom=max(frame.get_bounding_rect().bottom for frame in cells)
            width=max(frame.get_width() for frame in cells)
            for cell in cells:
                # Operation: A common canvas keeps every expression's feet/handle
                #     aligned.
                # Input: Cell widths and the common painted vertical extent.
                # Output: Aligned frame surfaces that keep expression anchors stable.
                frame=pygame.Surface((width,bottom-top),pygame.SRCALPHA)
                frame.blit(cell,(0,-top))
                self.frames.append(frame)
        # Operation: Empty frames preserve the existing caller-selected missing-art
        #     fallback.
        # Input: Existing image/read/crop exception handling.
        # Output: Load failure retains the caller-selected missing-art route.
        except (pygame.error,OSError,ValueError):
            pass

    @lru_cache(maxsize=30)
    def scaled(self, index, width):
        """Return a cached aspect-preserving frame, or None if artwork is unavailable.

        Operation:
            Scale one extracted expression while preserving its aspect ratio.
        Input:
            index, width in pixels, and extracted frames.
        Output:
            Returns a cached Surface or None when frames are absent.
        """
        if not self.frames:return None
        frame=self.frames[index]
        return pygame.transform.smoothscale(frame,(width,round(width*frame.get_height()/frame.get_width())))

    def draw(self, screen, index, anchor, width):
        """Blit one expression at a midbottom scene-pixel anchor when available.

        Operation:
            Align a scaled expression to a scene-pixel midbottom anchor.
        Input:
            screen, index, anchor, width, and extracted frames.
        Output:
            Blits the frame when available; returns None.
        """
        frame=self.scaled(index,width)
        if frame is not None:screen.blit(frame,frame.get_rect(midbottom=anchor))


class SceneAssets:
    # Operation: Actual faces: closed/confident, smirk, open mouth, angry open mouth +
    #     vein, red-tinted anger. No separate surprised Knife face is present.
    # Input: Five inspected Knife faces; no separate surprised face exists.
    # Output: Reaction mapping uses the closest available angry frame for a correct
    #     answer.
    """Cache artwork and preserve courtroom occlusion and expression placement.

    Operation:
        Cache source art, fallback portraits, and aligned foreground occlusion.
    Input:
        Configured image paths and scene dimensions.
    Output:
        Provides cached surfaces and court composition without changing source assets.
    """

    KNIFE_EXPRESSIONS={'talking':2,'waiting':0,'shocked':3,'smug':1}

    def __init__(self):
        """Load source artwork and precompute Chef portraits and board shadow.

        Operation:
            Prepare strips, background, board, Chef reactions, and board shadow.
        Input:
            Settings and initialized Pygame display.
        Output:
            Sets asset caches with existing fallbacks; returns None.
        """
        self.knife=SpriteStrip(s.KNIFE_ASSET)
        self.tomato=SpriteStrip(s.ROOT/'assets/Tomato_SpriteSheet.png')
        self.background=self.load_background()
        self.board=self.load_board()
        self.chef=Chef(s.ROOT/'assets/Chef_SpriteSheet.png')
        self.chef_expression='listening'
        self.board_shadow=self.make_shadow((s.BOARD_RECT[2],s.BOARD_RECT[3]))

    def load_background(self):
        """Return a centered aspect-cover background, or the existing drawn fallback.

        Operation:
            Scale the source to cover the scene, preserving aspect and centered crop.
        Input:
            COURTROOM_ASSET and scene dimensions.
        Output:
            Returns background Surface; caught image/read errors return the existing
            drawn fallback.
        """
        try:
            source=pygame.image.load(str(s.COURTROOM_ASSET)).convert()
            scale=max(s.WIDTH/source.get_width(),s.HEIGHT/source.get_height())
            image=pygame.transform.smoothscale(source,(round(source.get_width()*scale),round(source.get_height()*scale)))
            result=pygame.Surface((s.WIDTH,s.HEIGHT))
            result.blit(image,image.get_rect(center=(s.WIDTH//2,s.HEIGHT//2 + 150)))
            return result
        except (pygame.error,OSError):
            result=pygame.Surface((s.WIDTH,s.HEIGHT));result.fill('#a87c50')
            pygame.draw.rect(result,'#63402e',s.CENTRAL_BENCH_FOREGROUND)
            return result

    def load_board(self):
        """Return the aspect-preserved rotated board with its white exterior removed.

        Operation:
            Remove inspected white exterior/handle pixels, rotate, and scale
            proportionally.
        Input:
            BOARD_ASSET, alpha threshold, and BOARD_RECT width.
        Output:
            Returns a board Surface; caught read/format/crop failures return drawn wood.
            Character highlights are never keyed out.
        """
        try:
            image=pygame.image.load(str(s.BOARD_ASSET)).convert_alpha()
            # Operation: This inspected JPEG has a white exterior and white handle hole,
            #     and no white painted details on the board. This operation is only for
            #     the board; character eyes/highlights retain source alpha.
            # Input: Board JPEG with white exterior/hole and no intentional white wood
            #     details.
            # Output: Board-only alpha mask; character eyes and highlights keep source
            #     alpha.
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
        """Return the existing layered shadow for a board size measured in pixels.

        Operation:
            Layer the existing rounded translucent rectangles around the board size.
        Input:
            size: board width/height in scene pixels.
        Output:
            Returns a shadow Surface; no source assets are modified.
        """
        shadow=pygame.Surface((size[0]+32,size[1]+32),pygame.SRCALPHA)
        for inset in range(16,0,-2):
            pygame.draw.rect(shadow,(25,13,5,3+(16-inset)),(16-inset,16-inset,size[0]+inset*2,size[1]+inset*2),border_radius=50)
        return shadow

    def update_chef(self, dt, expression):
        if expression != self.chef_expression:
            self.chef_expression=expression
            if expression=='listening':
                self.chef.reset()
            else:
                self.chef.play()
        self.chef.update(dt)

    def draw_courtroom(self, screen, session):
        """Draw background, Chef, bench occlusion, actors, then foreground desks.

        Operation:
            Layer background, Chef, aligned bench occlusion, actors, then desks.
        Input:
            screen; session reactions/stage/banner time; cached surfaces and anchors.
        Output:
            Renders the court, preserving mistake red frame and decaying Tomato shake;
            returns None.
        """
        screen.blit(self.background,(0,0))
        # Operation: Reuse precisely the same transformed background pixels for the
        #     bench before drawing the full Chef sprite over it.
        # Input: Transformed background and bench rectangle.
        # Output: Bench area is restored without covering the Chef sprite's own counter.
        bench=pygame.Rect(s.CENTRAL_BENCH_FOREGROUND)
        screen.blit(self.background,bench,bench)
        self.chef.draw(screen,s.CHEF_ANCHOR,s.CHEF_PORTRAIT_SIZE)
        for anchor,width in ((s.KNIFE_ANCHOR,350),(s.TOMATO_ANCHOR,180)):
            shadow=pygame.Surface((width,20),pygame.SRCALPHA)
            pygame.draw.ellipse(shadow,(32,15,6,55),(0,0,width,20))
            screen.blit(shadow,(anchor[0]-width//2,anchor[1]-14))
        if self.knife.frames:
            self.knife.draw(screen,self.KNIFE_EXPRESSIONS[session.gadget_expression],s.KNIFE_ANCHOR,s.KNIFE_WIDTH)
        else:
            pygame.draw.polygon(screen,'#b7b9b5',[(90,590),(265,590),(290,540),(110,540)])
        # Operation: Preserve the mistake-only red frame and shake independently of HP
        #     expression.
        # Input: Stage, HP-selected expression, and banner elapsed/duration seconds.
        # Output: Existing red mistake frame and decaying shake; other frames retain
        #     their anchors.
        if self.tomato.frames:
            index=4 if session.stage=='MISTAKE_ANIMATION' else TOMATO_FRAMES[session.tomato_expression]
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
        # Operation: Desks are the final actor occluder, using the identical background
        #     transform.
        # Input: Foreground desk rectangle and transformed background.
        # Output: Desk pixels cover actor lower edges without changing other layers.
        desk=pygame.Rect(s.FRONT_DESK_FOREGROUND)
        screen.blit(self.background,desk,desk)
