"""Single room exit flow: active -> cleared -> reward -> leaving (or dead)."""
from game.entities.triggers.trigger import Trigger
from game.ui.room_reward_card import RoomRewardCard


class RoomCompletion:
    def __init__(self, screen):
        self.screen = screen
        self.result = screen.game.run_state.begin_room()

    @property
    def complete(self):
        return self.result.phase in ('cleared', 'reward', 'leaving')

    def update(self):
        screen = self.screen
        if self.result.phase in ('dead', 'leaving', 'reward'):
            return
        # Death wins when the player and last enemy die in the same update.
        if screen.player.health <= 0:
            self.result.phase = 'dead'
            from game.screens.game_over_screen import GameOverScreen
            screen.game.screen_manager.set_screen(GameOverScreen(screen.game))
            return
        screen.remove_dead_enemies()
        boss = getattr(screen, 'boss', None)
        if screen.room.room_type == 'boss' and (boss is None and not screen.enemies or boss is not None and boss.is_dead()):
            if not self.result.boss_revealed and screen.game.run_state.mode != 'boss_test':
                self.result.boss_revealed = True
                screen.tower_track.defeat_boss(screen.game.run_state.run_cycles+1, screen.game.run_state.max_cycles)
                screen.game.run_state.tower_history.save()
        if self.result.phase == 'active' and not screen.enemies:
            self.result.phase = 'cleared'
            screen.room.cleared = True
            screen.room.open_doors()
            screen.triggers = [Trigger(rect) for rect in screen.room.trigger_spawns]
            screen.triggers_spawned = True
        if self.result.phase == 'cleared':
            for trigger in screen.triggers:
                if screen.player.circle_collides_with_rect(trigger.rect):
                    reward = screen.game.run_state.grant_room_reward(self.result, screen.room_time, screen.combat_coins)
                    if reward is not None:
                        screen.reward_elapsed = 0
                        screen.reward_card = RoomRewardCard(reward, screen.game.localization)
                    break

    def confirm(self):
        screen = self.screen
        if (self.result.phase != 'reward' or screen.reward_card is None or
                screen.reward_elapsed < screen.reward_card.READY_AFTER or
                screen.game.screen_manager.current_screen is not screen):
            return
        self.result.phase = 'leaving'
        screen.game.finish_current_screen(screen)

    def reopen_for_debug(self):
        if self.result.reward is not None:
            return False
        self.result.phase = 'active'
        self.screen.room.cleared = False
        self.screen.triggers_spawned = False
        self.screen.triggers.clear()
        for door in self.screen.room.doors:
            door['open'] = False
        return True
