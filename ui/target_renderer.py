"""Upright label sprites with cached fractional-pixel translations.

Operation:
    Cache upright label sprites and apply fractional-pixel translations.
Input:
    UI wrapping/fonts, target display state, stage, count, mouse position, and raster
    settings.
Output:
    Rendered label pixels and caches; target simulation state is never advanced here.
"""
import math
from functools import lru_cache
import pygame
import settings as s


def label_font_size(count):
    """Return the existing font size for the visible answer count.

    Operation:
        Apply the existing dense-group threshold consistently.
    Input:
        count: visible answer count.
    Output:
        Returns 20 for more than three labels, otherwise 24; no state changes.
    """
    return 20 if count > 3 else 24


class TargetRenderer:
    """Cache upright label sprites and subpixel translations for shared motion.

    Operation:
        Cache upright label sprites and fractional coverage translations.
    Input:
        UI font/wrapping service and target raster/subpixel settings.
    Output:
        Provides render caches; does not own target motion.
    """

    def __init__(self, ui):
        """Bind UI wrapping and prepare fonts at the configured raster scale.

        Operation:
            Bind UI wrapping and allocate supersampled fonts.
        Input:
            ui and configured raster/subpixel scales.
        Output:
            Sets font/scaling caches; returns None.
        """
        self.ui = ui
        self.scale = s.TARGET_SUBPIXEL_SCALE
        self.raster_scale=s.TARGET_RASTER_SCALE
        self.fonts = {size: pygame.font.Font(None, size*self.raster_scale) for size in (20,24)}
        # Instance-owned caches let old scenes and their surfaces be collected when
        # the game restarts; decorating methods at class scope retains `self` globally.
        self.sprite = lru_cache(maxsize=32)(self._sprite)
        self.translated = lru_cache(maxsize=128)(self._translated)

    # Keep the rendered label cache small. At 260×100 pixels, a single RGBA
    # surface is about 100 KiB; the translation cache below is larger still.
    def _sprite(self, name, width, height, size, feedback, hover):
        """Return a cached premultiplied label for the requested size and visual state.

        Operation:
            Draw a supersampled label, then downsample and premultiply alpha.
        Input:
            name, width/height, font size, feedback, hover; UI wrapping and cached
            fonts.
        Output:
            Returns a cached native-size Surface; only render cache state changes.
        """
        scale = self.raster_scale
        surface = pygame.Surface((width*scale,height*scale),pygame.SRCALPHA)
        ink = '#503522'
        fill = '#bce3c6' if feedback=='correct' else '#f0b5ad' if feedback=='incorrect' else '#fff5dd'
        if hover:fill='#ffe4ab'
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
        # Operation: Build the text once at high resolution, then retain a native-size
        #     premultiplied sprite for inexpensive fractional translations.
        # Input: Supersampled label Surface and requested native size.
        # Output: Downsampled premultiplied sprite cached for fractional translations.
        return pygame.transform.smoothscale(surface,(width,height)).premul_alpha()

    # Positions can produce many subpixel phases over a long session. A bounded
    # cache is essential here: every entry owns a full-size RGBA Surface.
    def _translated(self, name, width, height, size, feedback, hover, phase_x, phase_y):
        """Return a cached fractional translation using four weighted native blits.

        Operation:
            Blend four weighted native offsets to represent fractional placement.
        Input:
            Label appearance parameters and integer phase_x/phase_y subpixel bins.
        Output:
            Returns a cached translated Surface without rotating or stretching text.
        """
        sprite=self.sprite(name,width,height,size,feedback,hover)
        surface=pygame.Surface((width+2,height+2),pygame.SRCALPHA)
        fx,fy=phase_x/self.scale,phase_y/self.scale
        # Operation: Bilinear coverage from four neighboring pixel offsets, in C-backed
        #     surface operations. Premultiplied alpha prevents dark/bright fringes.
        # Input: Native premultiplied sprite and fractional x/y phases.
        # Output: Four weighted offset blits blend coverage without dark or bright
        #     fringes.
        for dx,dy,weight in ((0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),
                             (0,1,(1-fx)*fy),(1,1,fx*fy)):
            if weight<=0:continue
            part=sprite.copy()
            value=round(255*weight)
            part.fill((value,value,value,value),special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(part,(dx,dy),special_flags=pygame.BLEND_RGBA_ADD)
        return surface

    def draw(self, screen, target, count, stage):
        """Blit a target at the exact interpolated position used by contains().

        Operation:
            Choose existing visual state and blit at the same fractional origin used by
            hit testing.
        Input:
            screen, target, count, stage, mouse position, and render caches.
        Output:
            Renders the label; may populate caches; does not modify motion; returns
            None.
        """
        feedback=target.feedback if stage=='FEEDBACK' else ''
        hover=stage=='ANSWERING' and target.contains(pygame.mouse.get_pos())
        size=label_font_size(count)
        # Operation: Fractional display position is also the hit-test origin; never snap
        #     it separately.
        # Input: Target draw_position, stage, count, and mouse position.
        # Output: Matching visual/hit-test origin; hover never modifies the simulation.
        x,y=target.draw_position
        floor_x,floor_y=math.floor(x),math.floor(y)
        phase_x=round((x-floor_x)*self.scale)
        phase_y=round((y-floor_y)*self.scale)
        # Rounding the final phase can reach `scale`; carry that pixel into the
        # integer origin so equivalent phases do not occupy separate cache slots.
        if phase_x >= self.scale:
            floor_x += 1
            phase_x = 0
        if phase_y >= self.scale:
            floor_y += 1
            phase_y = 0
        image=self.translated(target.name,target.width,target.height,size,feedback,hover,phase_x,phase_y)
        screen.blit(image,(floor_x,floor_y),special_flags=pygame.BLEND_PREMULTIPLIED)
