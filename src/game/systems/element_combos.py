from game.systems.impacts import Impact, apply_impact
import pygame


def create_thermal_fragments(bullet, enemy, combo_data):
    from game.entities.bullets.bullet import create_fragment

    fragment_count = combo_data["thermal_fragment_count"]

    if fragment_count <= 0:
        return []

    fragment_range = combo_data["thermal_fragment_range"]
    fragment_speed = combo_data["thermal_fragment_speed"]
    angle_step = 360 / fragment_count
    fragments = []

    for index in range(fragment_count):
        direction = pygame.Vector2(1, 0).rotate(angle_step * index)
        fragment = create_fragment(
            x=enemy.x + direction.x * (enemy.radius + 2),
            y=enemy.y + direction.y * (enemy.radius + 2),
            vel_x=direction.x * fragment_speed,
            vel_y=direction.y * fragment_speed,
            max_distance=fragment_range,
            damage=bullet.damage,
            elements=["fire", "ice"],
            effect_data=bullet.effect_data,
            color=(255, 137, 69),
            fragment_style="thermal_stalactite",
        )
        fragments.append(fragment)

    return fragments


def apply_fire_on_ice_combo(bullet, enemy, hit_damage):
    ice = enemy.status_effects["ice"]

    ice["is_ice"] = False
    ice["ice_timer"] = 0
    ice["is_slowed"] = False
    ice["slow_timer"] = 0
    ice["stacks"] = 0
    ice["ice_cooldown"] = ice["cooldown_value"]

    enemy.speed = enemy.base_speed
    enemy.color = enemy.base_color

    combo_data = bullet.effect_data["combos"]["fire_ice"]
    multiplier = combo_data["damage_multiplier"]
    apply_impact(enemy, Impact(hit_damage * multiplier, kind='combo', source=bullet))

    return create_thermal_fragments(bullet, enemy, combo_data)

ELEMENTAL_COMBOS = {
    ("fire", "ice"): apply_fire_on_ice_combo,
}
