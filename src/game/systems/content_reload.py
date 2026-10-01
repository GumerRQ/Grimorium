"""Stage edited content before replacing live data; failures keep the game intact."""
from copy import copy
import json
import pygame

from game import config
from game.systems import enemy_content
from game.rooms import destructible_data, destructible
from game.systems.content_loader import load_shop_content
from game.ui.health_hearts import reload_hearts
from game.utils.paths import asset_path, data_path
from game.visuals.tower_background import TowerBackground


def reload_content(game, combat=None):
    enemies = enemy_content.read_definitions()
    props = destructible_data.read_definitions()
    for key in enemies:
        enemy_content.load_visual(key, enemies)
    prop_images = {key: destructible.build_images(key, props) for key in props}
    shop = load_shop_content()
    if not all(shop):
        raise ValueError('Shop content needs at least one potion, power and book')
    prices = [next(iter(group.values()))['price'] for group in shop]
    # Validate shop art now, so a typo is reported here instead of at the next shop.
    for group in shop:
        for spec in group.values():
            asset = spec.get('asset')
            if asset:
                pygame.image.load(asset_path(asset))
    texts = json.loads(data_path('lang', game.localization.language+'.json').read_text(encoding='utf-8'))
    if not isinstance(texts, dict):
        raise ValueError('Language JSON must contain an object')
    hearts = pygame.image.load(asset_path('images', 'backgrounds', 'tower', 'health.png'))
    if hearts.get_width() < 3 or hearts.get_width() % 3:
        raise ValueError('health.png: expected three equally wide frames')
    layout = getattr(game, 'hud_layout', None)
    hud_images = {}
    if layout:
        for key, item in layout.items.items():
            if layout.is_image(key) and not item.get('deleted', False):
                hud_images[item['asset']] = pygame.image.load(layout.image_path(item['asset'])).convert_alpha()
    player_sprite = game.run_state.player.visual.sprite.reloaded()
    background = None
    if game.tower_background is not None:
        old = game.tower_background
        background = TowerBackground(old.total_floors, old.seed)
        for field in ('floor', 'target_floor', '_start_floor', '_elapsed', 'cloud_time'):
            setattr(background, field, getattr(old, field))
    # Validate authored effect PNGs before dropping their render caches.
    for path in asset_path('images', 'effects').glob('*.png'):
        pygame.image.load(path)
    staged_enemies = []
    staged_props = []
    room_art = None
    floor_images = []
    if combat:
        room_art = copy(combat.room)
        room_art.load_art()
        for floor in combat.room.floors:
            index, angle, flip_x, flip_y = combat.room.floor_variants[(floor['row'], floor['col'])]
            image = pygame.transform.rotate(room_art.floor_sprites[index], angle)
            floor_images.append(pygame.transform.flip(image, flip_x, flip_y))
        for enemy in combat.enemies:
            key = getattr(enemy, 'content_id', None)
            if key in enemies:
                staged = copy(enemy)
                enemy_content.apply_stats(staged, enemies[key], enemy.content_level, preserve_health=True)
                staged.visual = enemy_content.load_visual(key, enemies)
                staged_enemies.append((enemy, staged))
            elif key is None and enemy.visual:
                visual = copy(enemy.visual)
                visual.sprite = enemy.visual.sprite.reloaded()
                staged_enemies.append((enemy, None, visual))
        for prop in combat.room.destructibles:
            if prop.kind in props:
                intact, damaged, fragments = prop_images[prop.kind]
                center = (prop.position[0]+prop.intact.get_width()//2,
                          prop.position[1]+prop.intact.get_height()//2)
                position = intact.get_rect(center=center).topleft
                rect = intact.get_bounding_rect().move(position)
                staged_props.append((prop, intact, damaged, fragments, position, rect))
    # Commit only after all files, images and derived values were prepared.
    enemy_content._catalog = enemies
    # Seed the cache from the same validated data, without rereading mid-commit.
    destructible_data.install_definitions(props)
    destructible.images.cache_clear()
    config.POTION_DATA, config.POWER_DATA, config.BOOK_DATA = shop
    config.POTION_PRICE, config.POWER_PRICE, config.BOOK_PRICE = prices
    game.localization.texts = texts
    reload_hearts()
    game.run_state.player.visual.sprite = player_sprite
    if background is not None:
        game.tower_background = background
        if combat:
            combat.tower_background = background
    if layout:
        layout.image_cache = hud_images
        layout.scaled_cache.clear()
    for entry in staged_enemies:
        enemy, staged = entry[:2]
        if staged is None:
            enemy.visual = entry[2]
        else:
            for field in ('max_health', 'health', '_speed', 'base_speed', 'damage', 'body_damage', 'radius', 'visual'):
                setattr(enemy, field, getattr(staged, field))
            for field in enemies[enemy.content_id].get('shooting', {}):
                setattr(enemy, field, getattr(staged, field))
        enemy._hitbox_key = None
    for prop, intact, damaged, fragments, position, rect in staged_props:
        prop.intact, prop.damaged, prop.fragments = intact, damaged, fragments
        prop.position, prop.rect = position, rect
        prop.spec = props[prop.kind]
        prop.hits = min(prop.hits, prop.spec['hits_to_break']-1)
    if combat:
        combat.room.objects = [prop.rect for prop in combat.room.destructibles]
        for field in ('wall_sprites', 'corner_sprites', 'door_sprites', 'floor_sprites', 'floor_shadow_overlays'):
            setattr(combat.room, field, getattr(room_art, field))
        for floor, image in zip(combat.room.floors, floor_images):
            floor['sprite'] = image
    from game.visuals.effect_images import effect_image, effect_frame
    from game.visuals.burn_flames import flame_sprite
    from game.visuals.ice_block import ice_block_surfaces
    from game.visuals.poison_marks import poison_mark
    from game.visuals.poison_storm import cloud_sprite
    for cached in (effect_image, effect_frame, flame_sprite, ice_block_surfaces, poison_mark, cloud_sprite):
        cached.cache_clear()
