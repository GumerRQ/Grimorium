from game.systems.collision_shapes import circle_overlaps_entity
import math

import pygame

from game.systems.ice_puddle import IcePuddle
from game.visuals.ice_block import ICE_DESIGNS
from game.visuals.frost_wave import draw_frost_wave


class FrostWave:
    def __init__(self, source, ice_data, combo_data):
        self.x = source.x
        self.y = source.y
        self.source = source

        self.max_radius = ice_data["frost_wave_radius"]
        self.duration = ice_data["frost_wave_duration"]
        self.ice_data = ice_data
        self.combo_data = combo_data

        self.current_radius = 0
        self.timer = 0
        self.affected_enemies = set()
        self.finished = False

    def update(self, dt, enemies):
        self.timer += dt

        progress = min(self.timer / self.duration, 1)
        self.current_radius = self.max_radius * progress

        created_effects = self.apply_to_enemies(enemies)

        if self.timer >= self.duration:
            self.finished = True

        return created_effects

    def apply_to_enemies(self, enemies):
        created_effects = []

        for enemy in enemies:
            if (
                enemy.is_dead()
                or enemy is self.source
                or enemy in self.affected_enemies
            ):
                continue


            if not circle_overlaps_entity(self.x, self.y, self.current_radius, enemy):
                continue

            ice = enemy.status_effects["ice"]

            if ice["is_ice"] or ice["ice_cooldown"] > 0:
                continue

            self.affected_enemies.add(enemy)
            ice["stacks"] += 1

            if ice["stacks"] >= self.ice_data["max_ice_stacks"]:
                created_effects.extend(
                    freeze_enemy(
                        enemy,
                        self.ice_data,
                        self.combo_data,
                    )
                )
                continue

            ice["is_slowed"] = True
            ice["slow_timer"] = self.ice_data["slow_duration"]
            ice["multiplier"] = self.ice_data["slow_multiplier"]

        return created_effects

    def draw(self, surface):
        if self.current_radius <= 0:
            return

        progress = min(self.timer / self.duration, 1)
        draw_frost_wave(surface, self.x, self.y, self.current_radius, progress)


def freeze_enemy(enemy, ice_data, combo_data):
    ice = enemy.status_effects["ice"]

    if ice["ice_timer"] <= 0:
        ice["visual_variant"] = next(ICE_DESIGNS)
    ice["is_ice"] = True
    ice["cooldown_value"] = ice_data["ice_cooldown"]
    ice["ice_timer"] = ice_data["ice_duration"]
    ice["is_slowed"] = False
    ice["slow_timer"] = 0

    fragile = enemy.status_effects["fragile"]
    fragile["timer"] = combo_data["ice_poison"]["fragile_duration"]
    fragile["execute_base_threshold"] = combo_data["ice_poison"][
        "execute_base_threshold"
    ]
    fragile["execute_threshold_per_stack"] = combo_data["ice_poison"][
        "execute_threshold_per_stack"
    ]

    electric_combo = combo_data["ice_electric"]
    puddle_duration = (
        ice_data["ice_duration"]
        + electric_combo["puddle_duration_bonus"]
    )

    effects = [
        IcePuddle(
            enemy.x,
            enemy.y + enemy.radius * 0.45,
            enemy.radius,
            puddle_duration,
            electric_combo,
        )
    ]

    if ice_data["frost_wave_radius"] > 0:
        effects.append(
            FrostWave(
                enemy,
                ice_data,
                combo_data,
            )
        )

    return effects
