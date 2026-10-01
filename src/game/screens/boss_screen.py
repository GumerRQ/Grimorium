from game.entities.bosses.basic_boss import BasicBoss
from game.entities.bosses.leaping_boss import LeapingBoss
from game.rooms.room_data import get_random_boss_room
from game.screens.combat_screen import CombatScreen


class BossScreen(CombatScreen):
    def __init__(self, game, boss_type="leaping", room_layout=None):
        with game.content_random('boss'):
            super().__init__(game, room_layout if room_layout is not None else get_random_boss_room(), "boss")

            boss_class = BasicBoss if boss_type == "basic" else LeapingBoss
            self.boss = boss_class(self.game.run_state.enemy_level)

            if self.room.boss_spawn is not None:
                self.boss.x, self.boss.y = self.room.boss_spawn

            self.enemies = [self.boss]

    def draw_extra(self, surface):
        if not self.boss.is_dead():
            self.boss.draw_boss_health_bar(surface, self.font)
