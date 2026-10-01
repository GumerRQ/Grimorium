"""Keyboard/mouse development panel; the underlying room remains paused."""
import secrets
import pygame

from game.screens.base_screen import BaseScreen
from game.ui.fonts import create_font
from game.systems.enemy_content import definitions, create_enemy
from game.rooms import room_data
from game.rooms.custom_rooms import documents, validate


class DebugScreen(BaseScreen):
    VIRTUAL_WIDTH = 640
    VIRTUAL_HEIGHT = 360
    ACTIONS = ('seed', 'restart', 'random_seed', 'room', 'enemy', 'heal', 'hurt',
               'max_up', 'max_down', 'coins_up', 'coins_down', 'invulnerable',
               'clear', 'reload', 'resume')

    def __init__(self, game, previous):
        super().__init__(game)
        self.previous = previous
        self.font = create_font(10)
        self.selected = 0
        self.editing = False
        self.seed = game.run_state.run_seed
        self.room_index = self.enemy_index = 0
        self.status = ''
        self.refresh_choices()

    @property
    def combat(self):
        from game.screens.combat_screen import CombatScreen
        return self.previous if isinstance(self.previous, CombatScreen) else None

    def t(self, key):
        return self.game.localization.text('ui.debug.'+key)

    def refresh_choices(self):
        self.enemy_keys = list(definitions())
        self.rooms = [(name, 'normal', layout) for name, layout in vars(room_data).items()
                      if name.startswith('RANDOM_ROOM_')]
        self.rooms += [(name, 'boss', layout) for name, layout in vars(room_data).items()
                       if name.startswith('BOSS_ROOM_')]
        self.rooms += [(data.get('name', path.stem), data['type'], data['layout'])
                       for path, data in documents() if not validate(data['layout'], data['type'])]
        self.enemy_index %= max(1, len(self.enemy_keys))
        self.room_index %= max(1, len(self.rooms))

    def close(self):
        self.game.screen_manager.set_screen(self.previous)

    def on_exit(self):
        pygame.key.stop_text_input()

    def activate(self):
        action = self.ACTIONS[self.selected]
        player = self.game.run_state.player
        try:
            if action == 'seed':
                self.editing = True
                pygame.key.start_text_input()
            elif action == 'restart':
                self.game.start_new_run(self.seed)
            elif action == 'random_seed':
                self.seed = str(secrets.randbits(32))
            elif action == 'resume':
                self.close()
            elif action == 'reload':
                self.reload()
            elif action == 'room':
                self.load_room()
            elif action == 'enemy':
                self.spawn_enemy()
            elif action == 'clear':
                if self.combat:
                    for enemy in self.combat.enemies:
                        enemy.health = 0
                    self.combat.enemies.clear()
                    self.game.run_state.debug_used = True
            else:
                if not self.combat:
                    self.status = self.t('need_run')
                    return
                if action == 'heal': player.health = min(player.max_health, player.health+1)
                elif action == 'hurt': player.health = max(0, player.health-1)
                elif action == 'max_up': player.max_health += 2; player.health += 2
                elif action == 'max_down':
                    player.max_health = max(1, player.max_health-2)
                    player.health = min(player.health, player.max_health)
                elif action == 'coins_up': player.coins += 50
                elif action == 'coins_down': player.coins = max(0, player.coins-50)
                elif action == 'invulnerable': player.debug_invulnerable = not getattr(player, 'debug_invulnerable', False)
                self.game.run_state.debug_used = True
        except Exception as error:
            self.status = self.t('error') + ': ' + str(error)

    def load_room(self):
        from game.screens.play_screen import PlayScreen
        from game.screens.boss_screen import BossScreen
        if not self.combat:
            self.status = self.t('need_run')
            return
        _, kind, layout = self.rooms[self.room_index]
        screen = PlayScreen(self.game, layout) if kind == 'normal' else BossScreen(self.game, room_layout=layout)
        self.game.run_state.current_step = kind
        self.game.previous_room_layer = None
        self.previous = screen
        self.game.run_state.debug_used = True
        history = self.game.run_state.tower_history
        if history.floors:
            history.floors[-1].update(type=kind, layout=list(layout), completed=False)
            history.layers[-1] = screen.capture_room_layer(include_structure=False)
            history.debug_used = True
            history.save()
        self.status = self.t('room_loaded')

    def spawn_enemy(self):
        combat = self.combat
        if not combat or combat.room_reward is not None:
            self.status = self.t('need_room')
            return
        enemy = create_enemy((0, 0), self.game.run_state.enemy_level, self.enemy_keys[self.enemy_index])
        blockers = combat.get_blockers(True, True, True)
        for floor in sorted(combat.room.floors, key=lambda f: pygame.Vector2(f['rect'].center).distance_squared_to((combat.player.x, combat.player.y))):
            enemy.x, enemy.y = floor['rect'].center
            if pygame.Vector2(enemy.x, enemy.y).distance_to((combat.player.x, combat.player.y)) < enemy.radius+combat.player.radius+16:
                continue
            if not enemy.collides_with_rects(blockers) and not enemy.collides_with_circles(combat.enemies):
                combat.enemies.append(enemy)
                combat.room_flow.reopen_for_debug()
                self.game.run_state.debug_used = True
                self.status = self.t('spawned')
                return
        self.status = self.t('no_space')

    def reload(self):
        from game.systems.content_reload import reload_content
        try:
            reload_content(self.game, self.combat)
            self.refresh_choices()
            self.game.run_state.debug_used = True
            self.status = self.t('reloaded')
        except Exception as error:
            self.status = self.t('reload_error') + ': ' + str(error)

    def cycle(self, direction):
        action = self.ACTIONS[self.selected]
        if action == 'room': self.room_index = (self.room_index+direction) % len(self.rooms)
        elif action == 'enemy': self.enemy_index = (self.enemy_index+direction) % len(self.enemy_keys)

    def handle_event(self, event):
        if self.editing:
            if event.type == pygame.TEXTINPUT:
                self.seed = (self.seed + ''.join(c for c in event.text if c.isascii() and (c.isalnum() or c in '-_')))[:40]
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                    self.editing = False
                    pygame.key.stop_text_input()
                elif event.key == pygame.K_BACKSPACE: self.seed = self.seed[:-1]
                elif event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL: self.seed = ''
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_F9): self.close()
            elif event.key == pygame.K_F5: self.reload()
            elif event.key == pygame.K_UP: self.selected = (self.selected-1) % len(self.ACTIONS)
            elif event.key == pygame.K_DOWN: self.selected = (self.selected+1) % len(self.ACTIONS)
            elif event.key == pygame.K_LEFT: self.cycle(-1)
            elif event.key == pygame.K_RIGHT: self.cycle(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE): self.activate()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = self.screen_to_virtual(event.pos)
            index = int((y-49)//17)
            if 20 <= x <= 620 and 0 <= index < len(self.ACTIONS):
                self.selected = index
                if event.button == 1:
                    if x > 590: self.cycle(1)
                    elif x < 42: self.cycle(-1)
                    else: self.activate()
                elif event.button in (3, 4): self.cycle(-1)
                elif event.button == 5: self.cycle(1)

    def draw(self, surface):
        surface.fill((20, 26, 33))
        def text(value, x, y, color=(228, 233, 221)):
            surface.blit(self.font.render(value, True, color), (x, y))
        text(self.t('title'), 22, 10, (241, 199, 113))
        player = self.game.run_state.player
        text(f'{self.t("current_seed")}: {self.game.run_state.run_seed}   HP {player.health:g}/{player.max_health:g}   $ {player.coins}', 22, 28)
        for index, action in enumerate(self.ACTIONS):
            y = 49+index*17
            pygame.draw.rect(surface, (59, 78, 77) if index == self.selected else (31, 41, 49), (20, y, 600, 15))
            value = self.t(action)
            if action == 'seed': value += ': ' + self.seed + ('_' if self.editing else '')
            elif action == 'room': value += ': ' + self.rooms[self.room_index][0]
            elif action == 'enemy': value += ': ' + self.enemy_keys[self.enemy_index]
            elif action == 'invulnerable': value += ': ' + self.t('on' if getattr(player, 'debug_invulnerable', False) else 'off')
            text(value, 45, y+3)
            if action in ('room', 'enemy'):
                text('<', 26, y+3); text('>', 601, y+3)
        # Wrap failures rather than losing the relevant filename off-screen.
        for row in range(2): text(self.status[row*96:(row+1)*96], 22, 307+row*12, (241, 199, 113))
        text(self.t('help'), 22, 340)
