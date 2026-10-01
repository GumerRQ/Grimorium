"""Editable destructible definitions, independent of rendering and combat."""
import json
import math

from game.utils.paths import asset_path, data_path


_catalog = None


def definitions():
    global _catalog
    if _catalog is None:
        _catalog = read_definitions()
    return _catalog


def install_definitions(catalog):
    global _catalog
    _catalog = catalog


def read_definitions():
    path = data_path('game', 'destructibles.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    result = {}
    for kind, entry in data.items():
        if not entry.get('enabled', True):
            continue
        spec = dict(entry)
        for field in ('hits_to_break', 'damaged_after_hits'):
            if type(spec.get(field)) is not int or spec[field] < 1:
                raise ValueError(f'{kind}: {field} must be a positive integer')
        if spec['damaged_after_hits'] > spec['hits_to_break']:
            raise ValueError(f'{kind}: damaged state must precede destruction')
        for field in ('weight', 'body_hit_interval'):
            value = spec.get(field)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(f'{kind}: invalid {field}')
        frame = spec.get('frame_size')
        if not isinstance(frame, list) or len(frame) != 2 or any(type(v) is not int or v < 1 for v in frame):
            raise ValueError(f'{kind}: frame_size must be [width, height]')
        for color in spec.get('background_colors', []):
            if len(color) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in color):
                raise ValueError(f'{kind}: invalid background color')
        coins = spec.get('coins', 0)
        if type(coins) is not int or coins < 0:
            raise ValueError(f'{kind}: coins must be a nonnegative integer')
        spec['coins'] = coins
        image = asset_path(spec['asset']).resolve()
        if not image.is_relative_to(asset_path().resolve()) or not image.is_file():
            raise ValueError(f'{kind}: missing or invalid asset')
        result[kind] = spec
    if not result or not any(spec['weight'] > 0 for spec in result.values()):
        raise ValueError('At least one destructible must have a positive weight')
    return result
