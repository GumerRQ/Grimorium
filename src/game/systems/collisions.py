"""Funciones de colision.

Separarlas aqui te ayuda a no mezclar estas reglas
con el codigo de dibujo o de menus.
"""

from game.systems.impacts import Impact, apply_impact
import math
from game.systems.collision_shapes import damage_bounds, overlap_area, circle_overlaps_entity
from game.systems.effect_handlers import ELEMENT_EFFECTS
from game.systems.element_combos import ELEMENTAL_COMBOS

from game.systems.poison_cloud import PoisonCloud


def circles_collide(a, b):
    # Keep the public entry point for bullets/effects; enemies now expose boxes.
    a_box, b_box = hasattr(a, "get_hitbox_bounds"), hasattr(b, "get_hitbox_bounds")
    if a_box and b_box:
        return overlap_area(damage_bounds(a), damage_bounds(b)) > 0
    if a_box or b_box:
        box, circle = (a, b) if a_box else (b, a)
        return circle_overlaps_entity(circle.x, circle.y, circle.radius, box)
    distance = math.hypot(a.x - b.x, a.y - b.y)
    return distance <= a.radius + b.radius

def separate_circles(a, b, blockers):
    if hasattr(a, "get_hitbox_bounds") or hasattr(b, "get_hitbox_bounds"):
        # Resolve contact with the same body boxes used to detect the hit.
        ab, bb = damage_bounds(a), damage_bounds(b)
        if overlap_area(ab, bb) <= 0:
            return
        pushes = ((bb[0] - ab[2], 0), (bb[2] - ab[0], 0),
                  (0, bb[1] - ab[3]), (0, bb[3] - ab[1]))
        dx, dy = min(pushes, key=lambda p: abs(p[0]) + abs(p[1]))
        for entity, sign in ((a, 1), (b, -1)):
            old_x, old_y = entity.x, entity.y
            entity.x += sign * dx / 2
            entity.y += sign * dy / 2
            if entity.collides_with_rects(blockers):
                entity.x, entity.y = old_x, old_y
        return
    dx = b.x - a.x
    dy = b.y - a.y
    distance = math.hypot(dx, dy)
    min_distance = a.radius + b.radius

    if distance == 0:
        dx = 1
        dy = 0
        distance = 1

    if distance >= min_distance:
        return

    overlap = min_distance - distance
    normal_x = dx / distance
    normal_y = dy / distance

    push_x = normal_x * (overlap / 2)
    push_y = normal_y * (overlap / 2)

    new_ax = a.x - push_x
    new_ay = a.y - push_y
    new_bx = b.x + push_x
    new_by = b.y + push_y

    old_ax, old_ay = a.x, a.y
    a.x, a.y = new_ax, new_ay

    if a.collides_with_rects(blockers):
        a.x, a.y = old_ax, old_ay

    old_bx, old_by = b.x, b.y
    b.x, b.y = new_bx, new_by

    if b.collides_with_rects(blockers):
        b.x, b.y = old_bx, old_by


def get_enemy_active_states(enemy):
    states = []

    if enemy.status_effects["burn"]["is_burned"]:
        states.append("burn")

    if enemy.status_effects["ice"]["is_ice"]:
        states.append("ice")

    return states


def try_apply_combo(bullet, enemy, element, hit_damage):
    active_states = get_enemy_active_states(enemy)

    for state in active_states:
        combo_handler = ELEMENTAL_COMBOS.get((element, state))
        if combo_handler is not None:
            return True, combo_handler(bullet, enemy, hit_damage)

    return False, None

def create_poison_cloud_if_needed(bullet, enemy):
    burn = enemy.status_effects["burn"]
    poison = enemy.status_effects["poison"]

    if poison["stacks"] <= 0:
        return None

    if burn["timer"] <= 0:
        return None

    combo_data = bullet.effect_data.get(
        "combos",
        {},
    ).get("fire_poison")

    poison_data = bullet.effect_data.get("poison")

    if combo_data is None or poison_data is None:
        return None

    cloud_float_height = max(
        combo_data["cloud_float_height"],
        combo_data["cloud_radius"]
        * combo_data["cloud_float_radius_multiplier"],
    )

    return PoisonCloud(
        enemy.x,
        enemy.y - cloud_float_height,
        combo_data,
        poison_data,
        rain_origin_y=enemy.y,
    )

def resolve_player_bullets_vs_enemies(bullets, enemies, blockers, damage_multiplier=1):
    bullets_left = []
    enemies_left = enemies[:]
    points_gained = 0
    created_effects = []

    for bullet in bullets:
        bullet_hit = False
        damage = bullet.damage * damage_multiplier

        for enemy in enemies_left[:]:
            if circles_collide(bullet, enemy):
                apply_impact(enemy, Impact(damage, source=bullet, knockback=(bullet.vel_x, bullet.vel_y), strength=83))

                for element in bullet.elements:
                    combo_applied, combo_effect = try_apply_combo(
                        bullet,
                        enemy,
                        element,
                        damage,
                    )

                    if combo_applied:
                        if combo_effect:
                            created_effects.extend(combo_effect)
                        continue

                    effect = ELEMENT_EFFECTS.get(element)
                    if effect is not None:
                        created_effect = effect(bullet, enemy, enemies_left, damage)

                        if created_effect is not None:
                            if isinstance(created_effect, list):
                                created_effects.extend(created_effect)
                            else:
                                created_effects.append(created_effect)

                bullet_hit = True

                if enemy.is_dead():
                    created_effect = create_poison_cloud_if_needed(bullet, enemy)

                    if created_effect is not None:
                        created_effects.append(created_effect)

                    enemies_left.remove(enemy)
                    points_gained += 0

                break

        if not bullet_hit:
            bullets_left.append(bullet)

    return bullets_left, enemies_left, points_gained, created_effects

def resolve_enemy_bullets_vs_player(enemy_bullets, player):
    bullets_left = []

    for bullet in enemy_bullets:
        if circles_collide(bullet, player):
            apply_impact(player, Impact(bullet.damage, source=bullet))
        else:
            bullets_left.append(bullet)

    return bullets_left


def resolve_enemies_touch_player(enemies, player, blockers):
    enemies_left = []
    points = 0

    for enemy in enemies:
        if getattr(enemy, "contact_disabled", False):
            enemies_left.append(enemy)
            continue
        if circles_collide(enemy, player):
            apply_impact(player, Impact(enemy.body_damage, kind='contact', source=enemy))

            if enemy.damage > 0:
                apply_impact(enemy, Impact(player.body_damage, kind='contact', source=player))

            separate_circles(player, enemy, blockers)

            if not enemy.is_dead():
                enemies_left.append(enemy)
            else:
                points += 0
        
        else:
            enemies_left.append(enemy)
            

    return enemies_left, points
