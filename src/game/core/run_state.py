"""Session-owned player, inventory and progression; screens do not own a run."""
from dataclasses import dataclass, field
import secrets

from game.entities.player import Player
from game.visuals.tower_history import TowerHistory


@dataclass
class RoomResult:
    phase: str = 'active'
    reward: dict = None
    boss_revealed: bool = False


@dataclass
class RunState:
    player: Player = field(default_factory=Player)
    run_seed: str = field(default_factory=lambda: str(secrets.randbits(32)))
    mode: str = 'menu'
    debug_used: bool = False
    run_step: int = 0
    current_step: str = None
    current_step_index: int = 0
    run_cycles: int = 0
    max_cycles: int = 3
    room_level: int = 1
    enemy_level: int = 1
    tower_history: TowerHistory = field(default_factory=TowerHistory)
    rooms: list = field(default_factory=list)

    def advance(self, pattern):
        self.current_step_index = self.run_step
        self.current_step = pattern[self.current_step_index]
        self.run_step = (self.run_step+1) % len(pattern)
        return self.current_step

    def finish_step(self, pattern):
        if self.current_step == 'normal':
            self.room_level += 1
        if self.current_step in ('normal', 'boss'):
            self.enemy_level += 1
        last_combat = max(i for i, step in enumerate(pattern) if step != 'shop')
        if self.current_step_index == last_combat:
            self.run_cycles += 1
            if self.run_cycles >= self.max_cycles:
                return True
            self.room_level = 1
        return False

    def floor_index(self, pattern):
        if self.mode == 'boss_test':
            return 0
        per_loop = sum(step in ('normal', 'boss') for step in pattern)
        earlier = sum(step in ('normal', 'boss') for step in pattern[:self.current_step_index])
        if self.current_step == 'shop':
            if earlier == per_loop:
                return max(0, self.run_cycles*per_loop-1)
            earlier = max(0, earlier-1)
        return self.run_cycles*per_loop+earlier

    def begin_room(self):
        result = RoomResult()
        self.rooms.append(result)
        return result

    def grant_room_reward(self, result, seconds, combat_coins):
        if result.reward is not None:
            return result.reward
        if result.phase != 'cleared' or self.player.health <= 0:
            return None
        savings = min(self.player.coins // 15, 3)
        health = int(self.player.health) // 2
        time = max(0, 5 - int(seconds / 5))
        bonus = savings + health + time
        self.player.coins += bonus
        result.reward = dict(enemies=combat_coins, savings=savings, health=health,
                             time=time, bonus=bonus, total=combat_coins+bonus,
                             wallet=self.player.coins, life=self.player.health, seconds=seconds)
        result.phase = 'reward'
        return result.reward

    def purchase(self, item, stock, apply_effect):
        if not any(candidate is item for candidate in stock):
            return 'unavailable'
        if self.player.coins < item['price']:
            return 'poor'
        apply_effect(self.player, item['id'])
        self.player.coins -= item['price']
        stock.remove(item)
        return 'bought'
