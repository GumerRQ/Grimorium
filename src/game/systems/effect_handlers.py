from game.systems.impacts import Impact, apply_impact
import math
from game.systems.electric_chain import ElectricChain
from game.systems.frost_wave import freeze_enemy


def apply_fire_data(enemy, fire_data):
    burn = enemy.status_effects["burn"]

    if not burn["is_burned"]:
        burn["is_burned"] = True
        burn["timer"] = fire_data["burn_duration"]
        burn["tick_timer"] = fire_data["burn_tick_timer"]
        burn["damage"] = fire_data["burn_damage"]
        burn["stacks"] = 1
        burn["hits_to_next_stack"] = 0
        burn["max_stacks"] = fire_data["max_burn_stacks"]
        return

    has_accumulated_combustion = (
        fire_data["max_burn_stacks"] > 1
    )

    if has_accumulated_combustion:
        burn["timer"] = fire_data["burn_duration"]

    if burn["stacks"] >= fire_data["max_burn_stacks"]:
        return

    burn["hits_to_next_stack"] += 1

    if burn["hits_to_next_stack"] < fire_data["burn_hits_per_stack"]:
        return

    burn["stacks"] += 1
    burn["hits_to_next_stack"] = 0

    burn["damage"] = (
        fire_data["burn_damage"]
        * burn["stacks"]
    )


def apply_fire_effect(bullet, enemy, _enemies, _hit_damage):
    apply_fire_data(enemy, bullet.effect_data["fire"])
    

def apply_ice_effect(bullet, enemy, _enemies, _hit_damage):
    ice_data = bullet.effect_data["ice"]
    ice = enemy.status_effects["ice"]

    if ice["ice_cooldown"] > 0 or ice["is_ice"]:
        return

    ice["stacks"] += 1

    if ice["stacks"] >= ice_data["max_ice_stacks"]:
        return freeze_enemy(
            enemy,
            ice_data,
            bullet.effect_data["combos"],
        )

    ice["is_slowed"] = True
    ice["slow_timer"] = ice_data["slow_duration"]
    ice["multiplier"] = ice_data["slow_multiplier"]


def apply_electric_effect(bullet, enemy, _enemies, hit_damage):
    electric_data = bullet.effect_data["electric"]

    damage = hit_damage * electric_data["damage_percentage"]
    max_jumps = electric_data["max_targets"]
    max_jump_distance = electric_data["max_jump_distance"]
    can_second_discharge = (
        electric_data["second_discharge_chains"] > 0
    )

    return ElectricChain(
        source=enemy,
        damage=damage,
        max_jumps=max_jumps,
        max_jump_distance=max_jump_distance,
        can_second_discharge=can_second_discharge,
    )


def apply_poison_effect(bullet, enemy, _enemies, _hit_damage):
    apply_poison_data(
        enemy,
        bullet.effect_data["poison"],
        bullet.effect_data["combos"]["ice_poison"],
    )


def apply_poison_data(enemy, poison_data, ice_poison_data):
    poison = enemy.status_effects["poison"]

    poison["max_stacks"] = poison_data["max_stacks"]
    poison["damage_taken_per_stack"] = poison_data["damage_taken_per_stack"]
    poison["boss_stack_decay_interval"] = poison_data[
        "boss_stack_decay_interval"
    ]
    poison["stacks"] = min(poison["stacks"] + 1, poison["max_stacks"])

    sentence_enemy_if_needed(
        enemy,
        poison,
        ice_poison_data,
    )

    try_execute_fragile_enemy(enemy, ice_poison_data)

    if getattr(enemy, "is_boss", False):
        poison["timer"] = poison_data["boss_duration"]
        poison["stack_decay_timer"] = 0
        poison["is_stack_decay_active"] = False


def sentence_enemy_if_needed(enemy, poison, combo_data):
    fragile = enemy.status_effects["fragile"]

    if (
        combo_data["sentence_enabled"] <= 0
        or fragile["timer"] <= 0
        or poison["stacks"] < poison["max_stacks"]
    ):
        return

    fragile["is_sentenced"] = True
    fragile["sentence_threshold"] = (
        combo_data["execute_base_threshold"]
        + poison["stacks"] * combo_data["execute_threshold_per_stack"]
    )


def try_execute_fragile_enemy(enemy, combo_data):
    fragile = enemy.status_effects["fragile"]

    if fragile["timer"] <= 0:
        return

    # Sentencia se resuelve desde take_damage para que cualquier fuente de
    # daño pueda activarla. La marca queda visible hasta ese siguiente daño.
    if fragile["is_sentenced"]:
        return

    # Una vez preparada la ejecución, el siguiente impacto de veneno mata.
    # No se ejecuta al preparar el estado: así se llega a dibujar la marca.
    if fragile["is_ready_to_execute"]:
        apply_impact(enemy, Impact(kind='execution', execute=True))
        return

    poison = enemy.status_effects["poison"]
    stacks = poison["stacks"]

    if stacks <= 0:
        return

    execute_threshold = (
        combo_data["execute_base_threshold"]
        + stacks * combo_data["execute_threshold_per_stack"]
    )

    health_ratio = enemy.health / enemy.max_health

    if health_ratio <= execute_threshold:
        fragile["is_ready_to_execute"] = True


ELEMENT_EFFECTS = {
    "fire": apply_fire_effect,
    "ice": apply_ice_effect,
    "electric": apply_electric_effect,
    "poison": apply_poison_effect,
}
