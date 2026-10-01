import pygame

from game import config
from game.systems.combat_effects import CombatEffects
from game.rooms.room import Room
from game.screens.base_screen import BaseScreen
from game.ui.fonts import create_font
from game.systems.collisions import (
    resolve_player_bullets_vs_enemies,
    resolve_enemy_bullets_vs_player,
    resolve_enemies_touch_player,
)

from game.systems.room_completion import RoomCompletion
from game.ui.actions import is_confirmation


WEAPON_KEYS = {
    pygame.K_1: "normal",
    pygame.K_2: "gatling",
    pygame.K_3: "spread",
}

class CombatScreen(BaseScreen):
    CAN_PAUSE = True
    VIRTUAL_WIDTH = 640
    VIRTUAL_HEIGHT = 360
    def __init__(self, game, room_layout, room_type):
        super().__init__(game)

        from game.ui.hud_layout import HudLayout
        if not hasattr(game, "hud_layout"):
            game.hud_layout = HudLayout()
        self.hud_layout = game.hud_layout

        # Combat background
        self.setup_background()

        self.setup_player_for_combat()

        self.bullets = []
        self.effects = CombatEffects(self)

        self.enemies = []
        self.enemies_bullets = []
        self.font = create_font(9)

        self.room = Room(room_layout, room_type, self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT)
        self.place_player_at_spawn()

        self.room_flow = RoomCompletion(self)

        self.triggers = []
        self.triggers_spawned = False

        self.intro_active = True
        self.intro_speed = 70
        self.setup_room_intro()

        self.room_time = 0
        self.combat_coins = 0
        self.reward_elapsed = 0.0
        self.reward_card = None

        self.stat_positions = {
            "coins": (58, 97),
            "health": (0, 0),
            "damage": (60, 121),
            "speed": (60, 143),
            "fire_rate": (60, 163),
            "shoot_distance": (60, 183),
            "body_damage": (60, 205),
            "luck": (0, 0),
        }

        self.setup_floor_track()

    def setup_background(self):
        self.tower_background = self.game.get_tower_background()
        self.tower_background.set_floor(self.game.get_tower_floor_index())
    def setup_player_for_combat(self):
        self.player = self.game.run_state.player
        self.player.visual.set_size(32, 32)
        self.player.visual.clear_fixed_frame()
        self.player.visual.set_locked(False)
        self.player.visual.set_state("idle", reset=True)
        self.player.visual.set_facing("down")


    def setup_floor_track(self):
        self.tower_track = self.game.run_state.tower_history.track

    def get_blockers(self, include_walls=True, include_objects=True, include_voids=False):
        return self.room.get_blocking_rects(include_walls, include_objects, include_voids)


    def setup_room_intro(self):
        if self.room.player_spawn is None:
            self.intro_active = False
            return

        entrance_door = self.room.get_entrance_door()

        if entrance_door is None:
            self.intro_active = False
            return

        self.intro_target_x, self.intro_target_y = self.get_intro_target_from_door(entrance_door)

        self.player.x = entrance_door["full_rect"].centerx
        self.player.y = entrance_door["full_rect"].centery

        self.player.visual.set_facing("up")
        self.player.visual.set_state("walk", reset=True)


    def get_intro_target_from_door(self, door):
        x = door["full_rect"].centerx
        y = door["full_rect"].centery
        distance = config.ROOM_CELL_SIZE

        if door["side"] == "bottom":
            y -= distance
        elif door["side"] == "top":
            y += distance
        elif door["side"] == "left":
            x += distance
        elif door["side"] == "right":
            x -= distance

        return x, y

    def update_room_intro(self, dt):
        dx = self.intro_target_x - self.player.x
        dy = self.intro_target_y - self.player.y

        distance = (dx * dx + dy * dy) ** 0.5

        if distance <= 2:
            self.player.x = self.intro_target_x
            self.player.y = self.intro_target_y
            self.player.visual.set_state("idle", reset=True)
            self.room.close_entrance_doors()
            self.intro_active = False
            return

        self.player.x += dx / distance * self.intro_speed * dt
        self.player.y += dy / distance * self.intro_speed * dt
        self.player.visual.update(dt)

    def place_player_at_spawn(self):
        if self.room.player_spawn is not None:
            self.player.x, self.player.y = self.room.player_spawn

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
            if not getattr(event, "repeat", False):
                from game.screens.hud_editor_screen import HudEditorScreen
                self.game.screen_manager.set_screen(HudEditorScreen(self.game, self))
            return
        if self.room_reward is not None:
            mouse_pos = self.screen_to_virtual(event.pos) if hasattr(event, 'pos') else None
            if is_confirmation(event, self.reward_card.button, mouse_pos):
                self.room_flow.confirm()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_0:
            self.kill_all_enemies()
            return

        if event.type == pygame.KEYDOWN:
            self.handle_weapon_key(event.key)

    def go_to_menu(self):
        from game.screens.menu_screen import MenuScreen

        self.game.screen_manager.set_screen(MenuScreen(self.game))

    def handle_weapon_key(self, key):
        if key in WEAPON_KEYS:
            self.player.bullet_type = WEAPON_KEYS[key]

    def kill_all_enemies(self):
        self.enemies = []

    def update_player(self, dt, blockers):
        keys = pygame.key.get_pressed()
        self.player.move(keys, dt, blockers, [])
        self.player.update(dt)

    def update_player_shooting(self):
        self.effects.accept_shots(self.player.shoot(pygame.key.get_pressed()))

    def update_enemies(self, dt, blockers):
        wall_blockers = self.get_blockers(True, False, False)
        ground_blockers = self.get_blockers(True, False, True)

        for enemy in self.enemies:
            enemy.prop_room = self.room
            enemy_blockers = wall_blockers if getattr(enemy, "is_flying", False) else ground_blockers
            was_airborne = getattr(enemy, 'contact_disabled', False)
            new_bullets = enemy.update(self.player, dt, enemy_blockers, self.enemies, self.room)
            if was_airborne and not getattr(enemy, 'contact_disabled', False):
                for prop in tuple(self.room.destructibles):
                    if enemy.collides_with_rects([prop.rect]):
                        self.room.hit_object(prop, body=True)

            if new_bullets:
                self.enemies_bullets.extend(new_bullets)

    def update_projectiles(self, dt, blockers):
        blockers = self.get_blockers(True, False, False)

        for bullet in self.bullets:
            bullet.update(dt, blockers, room=self.room)
            self.effects.on_projectile(bullet)

        for enemy_bullet in self.enemies_bullets:
            enemy_bullet.update(dt, blockers, room=self.room)

        self.bullets = [
            bullet for bullet in self.bullets
            if not bullet.is_offscreen() and not bullet.destroyed
        ]

        self.enemies_bullets = [
            bullet for bullet in self.enemies_bullets
            if not bullet.is_offscreen() and not bullet.destroyed
        ]

    def resolve_collisions(self, blockers):
        self.bullets, self.enemies, coins_gained, created_effects = resolve_player_bullets_vs_enemies(
            self.bullets,
            self.enemies,
            blockers,
            self.player.damage,
        )
        self.player.coins += coins_gained
        self.combat_coins += coins_gained

        self.effects.add_all(created_effects)

        self.enemies_bullets = resolve_enemy_bullets_vs_player(
            self.enemies_bullets,
            self.player,
        )

        self.enemies, coins_gained = resolve_enemies_touch_player(
            self.enemies,
            self.player,
            blockers
        )
        self.player.coins += coins_gained
        self.combat_coins += coins_gained

    def remove_dead_enemies(self):
        self.enemies = [enemy for enemy in self.enemies if not enemy.is_dead()]

    def draw_scene(self, surface):
        self.tower_background.draw(surface)

        self.draw_world(surface)
        self.draw_entities(surface)
        self.draw_projectiles(surface)
        self.effects.draw_effects(surface)
        self.draw_extra(surface)

    def draw(self, surface):
        self.draw_scene(surface)
        self.draw_floor_track(surface)
        self.draw_room_info(surface)
        self.draw_hud(surface)
        if self.reward_card is not None:
            self.reward_card.draw(surface, self.reward_elapsed)

    def capture_room_layer(self, include_enemies=False, include_structure=True):
        layer = pygame.Surface((self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT), pygame.SRCALPHA)
        self.room.draw(layer, include_structure=include_structure)
        if include_enemies:
            for enemy in self.enemies:
                enemy.draw_ground_shadow(layer)
            for enemy in self.enemies:
                enemy.draw(layer)
        return layer

    def draw_world(self, surface):
        self.room.draw(surface)

        self.effects.draw_ground(surface)

    def draw_entities(self, surface):
        for enemy in self.enemies:
            enemy.draw_ground_shadow(surface)
        if self.room_reward is None:
            self.player.draw(surface)
        elif self.reward_elapsed < .22:
            departing = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self.player.draw(departing)
            departing.set_alpha(round(255 * (1 - self.reward_elapsed / .22)))
            surface.blit(departing, (0, 0))

        for enemy in self.enemies:
            enemy.draw(surface)

    def draw_projectiles(self, surface):
        for bullet in self.bullets:
            bullet.draw(surface)

        for enemy_bullet in self.enemies_bullets:
            enemy_bullet.draw(surface)

    def draw_room_info(self, surface):
        seconds = round(self.room_time, 1)
        time_key = "ui.combat.time_whole" if seconds >= 100 else "ui.combat.time"
        self.hud_layout.draw_text(surface, self.font,
                                  self.game.localization.text(time_key).format(seconds=seconds),
                                  "time", config.HUD_COLOR)

    def draw_floor_track(self, surface):
        self.hud_layout.health_capacity = self.player.max_health
        self.tower_track.draw(surface, self.game.run_state.tower_history, self.font,
                              self.game.get_tower_floor_index(), self.game.localization, self.hud_layout)
        self.hud_layout.draw_images(surface)
        self.tower_track.draw_labels(surface, self.font, self.game.get_tower_floor_index(),
                                    self.game.localization, self.hud_layout)

    def draw_extra(self, surface):
        pass

    def draw_hud(self, surface):

        self.player.draw_player_stats(surface, self.font, self.stat_positions, self.hud_layout)
        self.player.draw_player_health(surface, self.font, self.hud_layout)

    @property
    def complete(self):
        return self.room_flow.complete

    @property
    def room_reward(self):
        return self.room_flow.result.reward

    def update_player_phase(self, dt, blockers):
        self.update_player(dt, blockers)
        self.update_player_shooting()

    def update_projectile_phase(self, dt, blockers):
        self.update_projectiles(dt, blockers)
        self.effects.update_projectiles(dt)

    def update_enemy_phase(self, dt, blockers):
        self.update_enemies(dt, blockers)
        self.remove_dead_enemies()
        self.resolve_collisions(self.get_blockers(True, True, True))

    def update_effect_phase(self, dt):
        self.effects.update(dt)
        if self.room.object_coins:
            self.player.coins += self.room.object_coins
            self.room.object_coins = 0

    def update_room_state_phase(self):
        self.room_flow.update()

    def update_room_timer(self, dt):
        if self.room_flow.result.phase == 'active':
            self.room_time += dt

    def update(self, dt):
        self.tower_background.update(dt)
        self.tower_track.update(dt)
        if self.room_reward is not None:
            self.reward_elapsed += max(0.0, dt)
            return
        if self.intro_active:
            self.update_room_intro(dt)
            return

        self.room.update_objects(dt)
        blockers_full = self.get_blockers(True, True, True)
        blockers_projectiles = self.get_blockers(True, True, False)

        self.update_player_phase(dt, blockers_full)
        self.update_projectile_phase(dt, blockers_projectiles)
        self.update_enemy_phase(dt, blockers_full)
        self.update_effect_phase(dt)
        self.update_room_state_phase()
        self.update_room_timer(dt)

