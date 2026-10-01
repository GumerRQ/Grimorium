from game.systems.impacts import Impact, apply_impact
import math

from game.visuals.electric_discharge import ElectricImpact, draw_discharge


class ElectricChain:
    def __init__(
        self,
        source,
        damage,
        max_jumps,
        max_jump_distance,
        jump_duration=0.15,
        can_second_discharge=False,
        is_second_discharge=False,
    ):
        self.source = source
        self.target = None

        self.damage = damage
        self.max_jumps = max_jumps
        self.jumps_done = 0
        self.max_jump_distance = max_jump_distance

        self.jump_duration = jump_duration
        self.timer = 0
        self.can_second_discharge = can_second_discharge
        self.is_second_discharge = is_second_discharge

        self.visited = {source}
        self.finished = False

    def create_second_discharge(self):
        if not self.can_second_discharge or self.is_second_discharge:
            return []

        return [
            ElectricChain(
                source=self.source,
                damage=self.damage,
                max_jumps=self.max_jumps,
                max_jump_distance=self.max_jump_distance,
                jump_duration=self.jump_duration,
                can_second_discharge=False,
                is_second_discharge=True,
            )
        ]

    def find_next_target(self, enemies):
        possible_targets = []

        for enemy in enemies:
            if enemy in self.visited or enemy.is_dead():
                continue

            distance = math.hypot(
                enemy.x - self.source.x,
                enemy.y - self.source.y,
            )

            if distance <= self.max_jump_distance:
                possible_targets.append(enemy)

        if not possible_targets:
            return None

        return min(
            possible_targets,
            key=lambda enemy: math.hypot(
                enemy.x - self.source.x,
                enemy.y - self.source.y,
            ),
        )

    def update(self, dt, enemies):
        if self.finished:
            return []

        if self.target is None:
            self.target = self.find_next_target(enemies)

            if self.target is None:
                self.finished = True
                return self.create_second_discharge()

        visual_effects = []
        self.timer += dt

        if self.timer >= self.jump_duration:
            apply_impact(self.target, Impact(self.damage, kind='effect', source=self))
            visual_effects.append(ElectricImpact(self.target.x, self.target.y))

            self.visited.add(self.target)
            self.source = self.target
            self.target = None

            self.jumps_done += 1
            self.timer = 0

            if self.jumps_done >= self.max_jumps:
                self.finished = True
                return visual_effects + self.create_second_discharge()

        return visual_effects


    def draw(self, surface):
        if self.finished or self.target is None:
            return

        progress = min(self.timer / self.jump_duration, 1)

        start_x = self.source.x
        start_y = self.source.y

        end_x = start_x + (self.target.x - start_x) * progress
        end_y = start_y + (self.target.y - start_y) * progress

        seed = int(start_x * 31 + start_y * 17) + self.jumps_done * 101
        draw_discharge(surface, (start_x, start_y), (end_x, end_y), self.timer, seed)
