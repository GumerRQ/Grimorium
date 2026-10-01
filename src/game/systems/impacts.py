"""Common damage entry point. Targets retain their own resistance rules."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Impact:
    damage: float = 1
    kind: str = 'projectile'
    source: object = None
    knockback: tuple = (0, 0)
    strength: float = 0
    execute: bool = False


@dataclass(frozen=True)
class ImpactResult:
    accepted: bool
    killed: bool


def apply_impact(target, impact):
    """Apply a hit after collision detection; also usable by area effects."""
    if hasattr(target, 'receive_impact'):
        accepted = target.receive_impact(impact)
        return ImpactResult(accepted, target.is_dead())
    before = target.health
    if impact.execute:
        target.health = 0
        if hasattr(target, 'damage_flash_timer'):
            target.damage_flash_timer = .15
    else:
        target.take_damage(impact.damage)
    dx, dy = impact.knockback
    length = math.hypot(dx, dy)
    if length and impact.strength and hasattr(target, 'apply_knockback'):
        target.apply_knockback(dx/length, dy/length, impact.strength)
    return ImpactResult(target.health < before, target.health <= 0)
