"""Owns combat effect lifecycles, rendering layers and effect interactions."""
from game.entities.bullets.bullet import Bullet
from game.systems.voltaic_fragmentation import VoltaicFragmentation
from game.visuals.voltaic_rock import VoltaicRockBurst
from game.systems.poison_cloud import PoisonCloud
from game.systems.lava_drop import LavaDrop
from game.systems.ice_puddle import IcePuddle
from game.systems.toxic_overload import ToxicOverload
from game.systems.toxic_trail import ToxicTrail


class CombatEffects:
    def __init__(self, combat):
        self.combat = combat
        self.combat_effects = []
        self.voltaic_fragmentations = []
        self.ice_puddles = []
        self.poison_clouds = []
        self.lava_drops = []
        self.toxic_overload = None
        self.toxic_trail = None
        self.routes = [(Bullet, 'bullets'), (IcePuddle, 'ice_puddles'),
                       (PoisonCloud, 'poison_clouds'), (LavaDrop, 'lava_drops'),
                       (VoltaicFragmentation, 'voltaic_fragmentations')]

    def add(self, effect):
        for effect_type, collection in self.routes:
            if isinstance(effect, effect_type):
                owner = self.combat if collection == 'bullets' else self
                getattr(owner, collection).append(effect)
                return
        self.combat_effects.append(effect)

    def add_all(self, effects):
        for effect in effects or ():
            self.add(effect)

    def update_projectiles(self, dt):
        self.electrify_ice_puddles()
        self.update_voltaic_fragmentations(dt)

    def update(self, dt):
        self.update_toxic_overload(dt)
        self.update_toxic_trail(dt)
        self.update_ice_puddles(dt)
        self.update_poison_clouds(dt)
        self.update_combat_effects(dt)

    def draw_ground(self, surface):
        if self.toxic_trail is not None:
            self.toxic_trail.draw(surface)
        if self.toxic_overload is not None:
            self.toxic_overload.draw(surface)
        for puddle in self.ice_puddles:
            puddle.draw(surface)

    def accept_shots(self, new_bullets):
        bullets_to_fire = []

        for bullet in new_bullets:
            elements = set(bullet.elements)
            is_toxic_overload_bullet = (
                "electric" in elements
                and "poison" in elements
            )

            if is_toxic_overload_bullet:
                if self.toxic_overload is None:
                    combo_data = bullet.effect_data["combos"]["electric_poison"]

                    self.toxic_overload = ToxicOverload(
                        self.combat.player,
                        combo_data,
                    )

                    if combo_data["trail_enabled"]:
                        if self.toxic_trail is None:
                            self.toxic_trail = ToxicTrail(
                                combo_data,
                                bullet.effect_data,
                            )

                    self.combat.player.toxic_overload_active = True
                    self.combat.player.toxic_overload_speed_multiplier = (
                        self.toxic_overload.speed_multiplier
                    )

                # Esta bala se consume y no se añade a bullets_to_fire.
                continue

            bullets_to_fire.append(bullet)

        self.combat.bullets.extend(bullets_to_fire)


    def on_projectile(self, bullet):
        self.ignite_poison_clouds(bullet)
        if bullet.hit_wall and self.has_voltaic_fragmentation(bullet):
            original_damage = bullet.damage * self.combat.player.damage

            effect = VoltaicFragmentation(
                bullet,
                original_damage,
                can_refragment=self.has_voltaic_refragmentation(bullet),
            )

            self.voltaic_fragmentations.append(effect)

        elif bullet.hit_wall and bullet.can_refragment:
            original_damage = bullet.damage * self.combat.player.damage

            effect = VoltaicFragmentation(
                bullet,
                original_damage,
                is_refragmentation=True,
            )

            self.voltaic_fragmentations.append(effect)


    def update_combat_effects(self, dt):
        new_effects = []

        for effect in self.combat_effects:
            created_effects = effect.update(dt, self.combat.enemies)

            if created_effects:
                new_effects.extend(created_effects)

        self.combat_effects = [
            effect for effect in self.combat_effects
            if not effect.finished
        ]

        self.add_all(new_effects)


    def has_voltaic_fragmentation(self, bullet):
        required_elements = {"fire", "electric"}

        return (
            required_elements.issubset(set(bullet.elements))
            and bullet.can_fragment
        )


    def has_voltaic_refragmentation(self, bullet):
        combo_data = bullet.effect_data.get("combos", {}).get(
            "fire_electric",
            {},
        )
        return combo_data.get("refragment_divisor", 0) > 0


    def update_voltaic_fragmentations(self, dt):
        new_fragments = []

        for effect in self.voltaic_fragmentations:
            fragments = effect.update(dt)
            new_fragments.extend(fragments)
            if effect.finished:
                self.combat_effects.append(VoltaicRockBurst(
                    effect.x, effect.y, effect.inward_direction, effect.is_refragmentation
                ))

        self.voltaic_fragmentations = [
            effect
            for effect in self.voltaic_fragmentations
            if not effect.finished
        ]

        self.combat.bullets.extend(new_fragments)


    def update_ice_puddles(self, dt):
        for enemy in self.combat.enemies:
            enemy.puddle_slow_multiplier = 1.0

        for puddle in self.ice_puddles:
            puddle.update(dt, self.combat.enemies)

        self.ice_puddles = [
            puddle for puddle in self.ice_puddles
            if not puddle.finished
        ]


    def update_poison_clouds(self, dt):
        new_lava_drops = []

        for cloud in self.poison_clouds:
            new_lava_drops.extend(cloud.update(dt, self.combat.enemies))

        self.poison_clouds = [
            cloud for cloud in self.poison_clouds
            if not cloud.expired
        ]

        self.lava_drops.extend(new_lava_drops)

        for lava_drop in self.lava_drops:
            lava_drop.update(dt, self.combat.enemies)

        self.lava_drops = [
            lava_drop for lava_drop in self.lava_drops
            if not lava_drop.finished
        ]


    def ignite_poison_clouds(self, bullet):
        if "fire" not in bullet.elements:
            return

        fire_data = bullet.effect_data.get("fire")

        for cloud in self.poison_clouds:
            if cloud.contains_entity(bullet):
                cloud.ignite(fire_data)


    def electrify_ice_puddles(self):
        for bullet in self.combat.bullets:
            if "electric" not in bullet.elements:
                continue

            for puddle in self.ice_puddles:
                if puddle.contains_entity(bullet):
                    puddle.electrify()


    def update_toxic_overload(self, dt):
        if self.toxic_overload is not None:
            self.toxic_overload.update(dt, self.combat.enemies)

            if self.toxic_overload.finished:
                self.toxic_overload = None
                self.combat.player.toxic_overload_active = False
                self.combat.player.toxic_overload_speed_multiplier = 1.0


    def update_toxic_trail(self, dt):
        if self.toxic_trail is None:
            return

        player = self.combat.player if self.toxic_overload is not None else None
        self.toxic_trail.update(dt, self.combat.enemies, player)

        if self.toxic_trail.finished:
            self.toxic_trail = None


    def draw_effects(self, surface):
        for cloud in self.poison_clouds:
            cloud.draw(surface)

        for lava_drop in self.lava_drops:
            lava_drop.draw(surface)

        for effect in self.voltaic_fragmentations:
            effect.draw(surface)

        for effect in self.combat_effects:
            effect.draw(surface)


