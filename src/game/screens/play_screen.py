from game.rooms.room_data import get_random_normal_room
from game.screens.combat_screen import CombatScreen
from game.systems.enemy_content import create_enemy


class PlayScreen(CombatScreen):
    def __init__(self, game, room_layout=None):
        with game.content_random('normal'):
            super().__init__(game, room_layout if room_layout is not None else get_random_normal_room(), 'normal')
            self.spawn_room_enemies()

    def spawn_room_enemies(self):
        for position in self.room.enemy_spawns:
            self.enemies.append(create_enemy(position, self.game.run_state.enemy_level))
