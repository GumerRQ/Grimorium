"""Pixel hearts: two health points per heart, one per half."""
import math
from functools import lru_cache

import pygame
from game.utils.paths import asset_path


@lru_cache(maxsize=1)
def heart_sheet():
    return pygame.image.load(asset_path('images', 'backgrounds', 'tower', 'health.png')).convert_alpha()


def heart_size():
    sheet = heart_sheet()
    return sheet.get_width() // 3, sheet.get_height()


def reload_hearts():
    heart_sheet.cache_clear()
    heart_image.cache_clear()


@lru_cache(maxsize=48)
def heart_image(halves, scale):
    # Sheet order: full, half, empty, with no space between frames.
    width, height = heart_size()
    image = heart_sheet().subsurface(((2-halves)*width, 0, width, height))
    return pygame.transform.scale(image, (width*scale, height*scale))


def heart_row_width(max_health, height):
    count = max(0, math.ceil(max_health / 2))
    frame_width, frame_height = heart_size()
    scale = max(1, height // frame_height)
    return max(0, count * (frame_width + 2) * scale - 2 * scale)


def draw_health_hearts(surface, health, max_health, rect, align='left'):
    rect = pygame.Rect(rect)
    count = max(0, math.ceil(max_health / 2))
    # Always grow rightwards in one row; never shrink or wrap the artwork.
    frame_width, frame_height = heart_size()
    scale = max(1, rect.height // frame_height)
    width, height, gap = frame_width*scale, frame_height*scale, 2*scale
    x = rect.left
    y = rect.y + (rect.height-height)//2
    remaining = max(0, math.ceil(min(health, max_health)))
    for index in range(count):
        halves = min(2, max(0, remaining-index*2))
        surface.blit(heart_image(halves, scale), (x, y))
        x += width+gap
