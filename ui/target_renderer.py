"""Upright label sprites with cached fractional-pixel translations.

Software blits normally discard fractional coordinates. Shift a supersampled
sprite before downsampling instead, so slow movement changes pixel coverage
smoothly rather than holding still and jumping a whole pixel.
"""
import math
from functools import lru_cache
import pygame
import settings as s


class TargetRenderer:
    def __init__(self, ui):
        self.ui = ui
        self.scale = s.TARGET_SUBPIXEL_SCALE
        self.raster_scale=s.TARGET_RASTER_SCALE
        self.fonts = {size: pygame.font.Font(None, size*self.raster_scale) for size in (20,24)}

    @lru_cache(maxsize=96)
    def sprite(self, name, width, height, size, feedback, hover):
        scale = self.raster_scale
        surface = pygame.Surface((width*scale,height*scale),pygame.SRCALPHA)
        ink = '#23384d'
        fill = '#bce3c6' if feedback=='correct' else '#f0b5ad' if feedback=='incorrect' else '#ffffff'
        if hover:fill='#fff0c7'
        rect=surface.get_rect()
        pygame.draw.rect(surface,fill,rect,border_radius=8*scale)
        pygame.draw.rect(surface,ink,rect,scale,border_radius=8*scale)
        lines=self.ui.wrap(name,width-16,size)
        if feedback:lines.append('CORRECT' if feedback=='correct' else 'YOUR PICK - INCORRECT')
        line_height=self.ui.fonts[size].get_linesize()*scale
        y=(height*scale-len(lines)*line_height)//2
        for line in lines:
            image=self.fonts[size].render(line,True,ink)
            surface.blit(image,((width*scale-image.get_width())//2,y))
            y+=line_height
        # Build the text once at high resolution, then retain a native-size
        # premultiplied sprite for inexpensive fractional translations.
        return pygame.transform.smoothscale(surface,(width,height)).premul_alpha()

    @lru_cache(maxsize=768)
    def translated(self, name, width, height, size, feedback, hover, phase_x, phase_y):
        sprite=self.sprite(name,width,height,size,feedback,hover)
        surface=pygame.Surface((width+2,height+2),pygame.SRCALPHA)
        fx,fy=phase_x/self.scale,phase_y/self.scale
        # Bilinear coverage from four neighboring pixel offsets, in C-backed
        # surface operations. Premultiplied alpha prevents dark/bright fringes.
        for dx,dy,weight in ((0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),
                             (0,1,(1-fx)*fy),(1,1,fx*fy)):
            if weight<=0:continue
            part=sprite.copy()
            value=round(255*weight)
            part.fill((value,value,value,value),special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(part,(dx,dy),special_flags=pygame.BLEND_RGBA_ADD)
        return surface

    def draw(self, screen, target, count, stage):
        feedback=target.feedback if stage=='FEEDBACK' else ''
        hover=stage=='ANSWERING' and target.contains(pygame.mouse.get_pos())
        size=20 if count>3 else 24
        x,y=target.draw_position
        floor_x,floor_y=math.floor(x),math.floor(y)
        phase_x=round((x-floor_x)*self.scale)
        phase_y=round((y-floor_y)*self.scale)
        image=self.translated(target.name,target.width,target.height,size,feedback,hover,phase_x,phase_y)
        screen.blit(image,(floor_x,floor_y),special_flags=pygame.BLEND_PREMULTIPLIED)
