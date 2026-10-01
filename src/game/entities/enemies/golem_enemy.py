from game.systems.enemy_content import load_visual
import math

from game import config
from game.entities.enemies.chaser_enemy import ChaserEnemy


class GolemEnemy(ChaserEnemy):
    # Two weight transfers per four-frame cycle. Mean speed stays unchanged.
    STRIDE_AMPLITUDE = 0.45
    MOVEMENT_SUBSTEP = 1 / 60
    FACING_HYSTERESIS = 1.2

    def __init__(self, position, level=1, definition=None):
        super().__init__(position, level)

        
        self.speed = config.ENEMY_SPEED * 0.5
        self.base_speed = self.speed
        self.radius = 13
        self.score_value = 20

        self.path_align_margin = 2
        self.path_arrival_distance = 10

        self.speed_animation = 0.45
        self._walk_time = 0.0
        self._stride_speed = None

        self.visual = load_visual(definition or 'golem')

    def _stride_integral(self, start, end):
        """Travel in base-speed seconds, integrated across frame boundaries."""
        omega = math.pi / self.speed_animation
        return end - start - self.STRIDE_AMPLITUDE * (
            math.sin(omega * end) - math.sin(omega * start)
        ) / omega

    def get_movement_speed(self):
        if self._stride_speed is not None:
            return self._stride_speed
        omega = math.pi / self.speed_animation
        return super().get_movement_speed() * (
            1 - self.STRIDE_AMPLITUDE * math.cos(omega * self._walk_time)
        )

    def move(self, player, dt, blockers, entities, room=None):
        self._movement_dt = dt
        if dt <= 0:
            return

        start_x, start_y = self.x, self.y
        speed = max(0.0, super().get_movement_speed())
        if speed <= 0 or self.base_speed <= 0:
            self.update_visual_from_movement(0, 0)
            return

        # Path visibility checks are expensive. Evaluate steering only once per
        # rendered update, never once per collision substep after a slow frame.
        self._stride_speed = speed
        try:
            move_x, move_y = self.get_requested_movement(player, dt, blockers, room)
        finally:
            self._stride_speed = None
        length = math.hypot(move_x, move_y)
        if length <= 1e-9:
            self.update_visual_from_movement(0, 0)
            return
        direction_x, direction_y = move_x / length, move_y / length
        other_entities = [entity for entity in entities if entity is not self]

        # Slow effects reduce both cadence and travel, keeping stride length fixed.
        cadence = speed / self.base_speed
        remaining_distance = self.navigator.remaining_distance
        remaining = dt
        while remaining > 1e-10:
            step_dt = min(
                remaining, self.MOVEMENT_SUBSTEP,
                self.radius * 0.25 / (speed * (1 + self.STRIDE_AMPLITUDE)),
            )
            end = self._walk_time + step_dt * cadence
            intended = self.base_speed * self._stride_integral(self._walk_time, end)
            step_distance = min(intended, remaining_distance)
            old_x, old_y = self.x, self.y
            self.move_by(direction_x * step_distance, direction_y * step_distance,
                         blockers, other_entities)

            travelled = math.hypot(self.x - old_x, self.y - old_y)
            if travelled <= 1e-9:
                # Nothing else can change during this update. Repeating the same
                # blocked collision for the remaining substeps cannot help.
                break
            if travelled > 1e-9:
                if travelled < intended - 1e-9:
                    # Sliding along an obstacle consumes only the accepted distance.
                    low, high = self._walk_time, end
                    for _ in range(24):
                        middle = (low + high) / 2
                        distance = self.base_speed * self._stride_integral(
                            self._walk_time, middle
                        )
                        if distance < travelled:
                            low = middle
                        else:
                            high = middle
                    end = (low + high) / 2
                self._walk_time = end % (4 * self.speed_animation)
            remaining_distance -= travelled
            if remaining_distance <= 1e-9:
                break
            remaining -= step_dt

        self.update_visual_from_movement(self.x - start_x, self.y - start_y)

    def update_animation(self, dt):
        # Movement owns the clock; wall time and knockback must not advance it again.
        # Keep the current pose while frozen, rather than snapping to the idle frame.
        if self.status_effects["ice"]["ice_timer"] > 0:
            return
        animation = self.visual.animator.get_current_animation()
        index = int(self._walk_time / self.speed_animation + 1e-9)
        frames = animation["frames"]
        self.visual.set_fixed_frame(frames[index % len(frames)], animation["row"])
