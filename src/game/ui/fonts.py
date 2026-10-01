import pygame

from assets.fonts.pixel_font import CHAR_H, CHAR_W, CHAR_WIDTHS, PixelFont
from game import config
from game.utils.paths import asset_path


class PixelGameFont:
    def __init__(self, scale):
        self.scale = max(1, scale)
        self.font = PixelFont(
            str(asset_path("fonts", config.PIXEL_FONT_IMAGE)),
            scale=self.scale,
        )
        self.advance_x = (CHAR_W + 1) * self.scale
        self.line_height = (CHAR_H + 2) * self.scale
        self._glyph_cache = {}

    def render(self, text, antialias, color, background=None):
        lines = text.splitlines() or [text]
        width = max((self._line_width(line) for line in lines), default=0)
        width = max(1, width)
        height = max(
            1,
            CHAR_H * self.scale + max(0, len(lines) - 1) * self.line_height
        )

        if background is None:
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
        else:
            surface = pygame.Surface((width, height))
            surface.fill(background)

        y = 0
        for line in lines:
            x = 0
            for char in line:
                glyph = None if char == "\u2009" else self._get_glyph(char, color)
                if glyph is not None:
                    surface.blit(glyph, (x, y))
                x += self._advance(char)
            y += self.line_height

        return surface

    def _advance(self, char):
        if char == "\u2009":
            return max(1, ((CHAR_WIDTHS.get(" ", CHAR_W) + 1) * self.scale) // 2)
        return (CHAR_WIDTHS.get(char, CHAR_W) + 1) * self.scale

    def _line_width(self, line):
        if not line:
            return 0

        width = 0
        for char in line:
            width += self._advance(char)

        return width - self.scale

    def _get_glyph(self, char, color):
        cache_key = (char, color)
        if cache_key not in self._glyph_cache:
            source = self.font.glyphs.get(char, self.font.glyphs.get("?"))
            if source is None:
                return None

            glyph = source.copy()
            glyph.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self._glyph_cache[cache_key] = glyph

        return self._glyph_cache[cache_key]


def create_font(size=None, pixel_scale=None):
    if config.FONT_FAMILY == "pixel":
        scale = pixel_scale if pixel_scale is not None else max(1, round(size / CHAR_H))
        return PixelGameFont(scale)
    return pygame.font.Font(None, size)
