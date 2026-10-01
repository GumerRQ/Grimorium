"""Enemy definitions and factory. Behavior stays in enemy classes."""
import json
import math
import random
from pathlib import Path

from game.utils.paths import data_path, asset_path
from game.visuals.animated_visual import AnimatedVisual

_catalog = None
BEHAVIORS = ('rat', 'goblin', 'golem', 'dragon')


def read_definitions():
    data = json.loads(data_path('game', 'enemies.json').read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not data:
        raise ValueError('enemies.json: expected a nonempty object')
    for key, spec in data.items():
        if spec.get('behavior') not in BEHAVIORS:
            raise ValueError(f'{key}: unknown behavior')
        for field in ('health', 'health_growth', 'speed', 'damage', 'body_damage', 'radius', 'weight'):
            value = spec.get(field)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(f'{key}: invalid {field}')
        if min(spec['health'], spec['health_growth'], spec['radius']) <= 0:
            raise ValueError(f'{key}: health, growth and radius must be positive')
        for field, value in spec.get('shooting', {}).items():
            if field not in ('shoot_cooldown', 'bullet_speed', 'shoot_distance', 'preferred_distance') or type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError(f'{key}: invalid shooting setting {field}')
        visual = spec['visual']
        path = asset_path('images', visual['image_folder'], visual['image_name']).resolve()
        if not path.is_relative_to(asset_path().resolve()) or not path.is_file():
            raise ValueError(f'{key}: missing sprite {path.name}')
        for field in ('frame_cols', 'frame_rows', 'scale_x', 'scale_y'):
            if type(visual.get(field)) is not int or visual[field] < 1:
                raise ValueError(f'{key}: invalid visual {field}')
        for animation in visual['animations'].values():
            if not 0 <= animation['row'] < visual['frame_rows'] or not animation['frames'] or any(not 0 <= frame < visual['frame_cols'] for frame in animation['frames']) or animation['speed'] <= 0:
                raise ValueError(f'{key}: invalid animation')
    if not any(s.get('enabled', True) and s['weight'] > 0 for s in data.values()):
        raise ValueError('At least one enemy needs a positive spawn weight')
    return data


def definitions():
    global _catalog
    if _catalog is None:
        _catalog = read_definitions()
    return _catalog


def load_visual(key, catalog=None):
    visual = AnimatedVisual(**(catalog if catalog is not None else definitions())[key]['visual'])
    sprite = visual.sprite
    width, height = sprite.sprite_sheet.get_size()
    if width % sprite.frame_cols or height % sprite.frame_rows:
        raise ValueError(f'{key}: sprite dimensions do not match the frame grid')
    return visual


def apply_stats(enemy, spec, level, preserve_health=False):
    ratio = enemy.health / enemy.max_health if preserve_health else 1
    enemy.max_health = max(1, int(spec['health'] * spec['health_growth'] ** (level-1)))
    enemy.health = min(enemy.max_health, max(0, ratio * enemy.max_health))
    enemy.speed = enemy.base_speed = spec['speed']
    enemy.damage, enemy.body_damage = spec['damage'], spec['body_damage']
    enemy.radius = spec['radius']
    for field, value in spec.get('shooting', {}).items():
        setattr(enemy, field, value)
    enemy._hitbox_key = None


def create_enemy(position, level=1, kind=None):
    from game.entities.enemies.rat_enemy import RatEnemy
    from game.entities.enemies.goblin_enemy import GoblinEnemy
    from game.entities.enemies.golem_enemy import GolemEnemy
    from game.entities.enemies.dragon_enemy import DragonEnemy
    catalog = definitions()
    if kind is None:
        keys = [k for k, s in catalog.items() if s.get('enabled', True) and s['weight'] > 0]
        kind = random.choices(keys, weights=[catalog[k]['weight'] for k in keys], k=1)[0]
    spec = catalog[kind]
    cls = dict(rat=RatEnemy, goblin=GoblinEnemy, golem=GolemEnemy, dragon=DragonEnemy)[spec['behavior']]
    enemy = cls(position, level, definition=kind)
    enemy.content_id, enemy.content_level = kind, level
    apply_stats(enemy, spec, level)
    return enemy
