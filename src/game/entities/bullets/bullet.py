"""Bala base."""

import pygame
import math
import random
from game import config
from game.entities.entity import Entity
from game.visuals.voltaic_rock import draw_voltaic_rock
from game.visuals.effect_images import effect_image
from game.rooms.destructible import sweep_rect



class Bullet(Entity):
    def __init__(
        self,
        x,
        y,
        vel_x,
        vel_y,
        color,
        radius,
        damage,
        rate,
        max_distance,
        elements=None,
        effect_data=None,
        world_width=None,
        world_height=None,
        fragment_style=None,
    ):
        super().__init__(x, y, radius, color)
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.damage = damage
        self.rate = rate
        self.max_distance = max_distance
        self.distance_traveled = 0
        self.destroyed = False

        self.elements = elements or []
        self.effect_data = effect_data or {}

        self.world_width = world_width
        self.world_height = world_height

        self.hit_wall = False
        self.can_fragment = True
        self.can_refragment = False
        self.fragment_direction = None

        self.impact_x = None
        self.impact_y = None

        self.visual_timer = 0
        self.fragment_style = fragment_style

    def update(self, dt, blockers, room=None):
        if self.destroyed:
            return
        if room is not None:
            self.update_room_collision(dt, blockers, room)
            return
        old_x = self.x
        old_y = self.y

        move_x = self.vel_x * dt
        move_y = self.vel_y * dt

        self.x += move_x
        self.y += move_y

        self.distance_traveled += math.hypot(move_x, move_y)

        if self.distance_traveled >= self.max_distance:
            self.destroyed = True

        if self.collides_with_rects(blockers):
            impact_x = self.x
            impact_y = self.y

            self.x = old_x + move_x
            self.y = old_y
            hit_x = self.collides_with_rects(blockers)

            self.x = old_x
            self.y = old_y + move_y
            hit_y = self.collides_with_rects(blockers)

            direction = pygame.Vector2(self.vel_x, self.vel_y)

            if hit_x:
                direction.x *= -1

            if hit_y:
                direction.y *= -1

            if direction.length_squared() > 0:
                direction = direction.normalize()

            self.fragment_direction = direction

            self.impact_x = impact_x
            self.impact_y = impact_y

            self.x = old_x
            self.y = old_y
            self.hit_wall = True
            self.destroyed = True
        
        self.visual_timer += dt

    def update_room_collision(self, dt, blockers, room):
        # Pick the first obstacle along the whole segment, including fast shots.
        distance = math.hypot(self.vel_x, self.vel_y)*dt
        remaining = max(0, self.max_distance-self.distance_traveled)
        fraction = min(1, remaining/distance) if distance else 1
        dx, dy = self.vel_x*dt*fraction, self.vel_y*dt*fraction
        closest = None
        candidates = [(rect, None) for rect in blockers]
        candidates.extend((prop.rect, prop) for prop in room.destructibles)
        for rect, prop in candidates:
            contact = sweep_rect(self.x, self.y, dx, dy, rect, self.radius)
            if contact is not None and (closest is None or contact[0] < closest[0]):
                closest = (contact[0], contact[1], prop)
        travel = closest[0] if closest is not None else 1
        self.x += dx*travel
        self.y += dy*travel
        self.distance_traveled += math.hypot(dx, dy)*travel
        self.visual_timer += dt
        if closest is not None:
            _, normal, prop = closest
            self.impact_x, self.impact_y = self.x, self.y
            self.destroyed = True
            if prop is not None:
                room.hit_object(prop)
            else:
                self.hit_wall = True
                direction = pygame.Vector2(self.vel_x, self.vel_y)
                if normal != (0, 0):
                    direction = direction.reflect(pygame.Vector2(normal))
                else:
                    direction *= -1
                self.fragment_direction = direction.normalize() if direction.length_squared() else direction
        elif self.distance_traveled >= self.max_distance:
            self.destroyed = True

    def is_offscreen(self):
        world_width = self.world_width if self.world_width is not None else config.SCREEN_WIDTH
        world_height = self.world_height if self.world_height is not None else config.SCREEN_HEIGHT

        return (
            self.x > world_width + self.radius
            or self.x < -self.radius
            or self.y > world_height + self.radius
            or self.y < -self.radius
        )
    
    def draw(self, surface):
        if self.fragment_style in ("voltaic_rock", "voltaic_stone"):
            draw_voltaic_rock(surface, self.x, self.y, max(3, self.radius + 1),
                              0.55 if self.fragment_style == "voltaic_rock" else 0,
                              self.visual_timer, angle=self.visual_timer * 180,
                              energized=self.fragment_style == "voltaic_rock")
            return
        if self.fragment_style == "thermal_stalactite":
            self.draw_thermal_stalactite(surface)
            return

        if "ice" in self.elements:
            pygame.draw.circle(surface, (120, 200, 255), (int(self.x), int(self.y)), self.radius + 4)

        if "poison" in self.elements:
            pygame.draw.circle(surface, (180, 80, 220), (int(self.x), int(self.y)), self.radius + 3)

        if "electric" in self.elements:
            self.draw_electric_sparks(surface)

        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def draw_thermal_stalactite(self, surface):
        if self.vel_x == 0 and self.vel_y == 0:
            return
        image = effect_image("13_estaca.png")
        angle = math.degrees(math.atan2(self.vel_y, self.vel_x))
        image = pygame.transform.rotate(image, -angle)
        surface.blit(image, image.get_rect(center=(round(self.x), round(self.y))))

    def draw_electric_sparks(self, surface):
        center = pygame.Vector2(self.x, self.y)

        # La forma cambia cada 0.06 segundos.
        frame = int(self.visual_timer / 0.08)
        rng = random.Random(frame)

        spark_count = 3

        for _ in range(spark_count):
            start_angle = rng.uniform(0, 360)
            end_angle = start_angle + rng.uniform(60, 130)

            start_direction = pygame.Vector2(1, 0).rotate(start_angle)
            end_direction = pygame.Vector2(1, 0).rotate(end_angle)

            # Ambas puntas tocan el borde de la bala.
            start = center + start_direction * self.radius
            end = center + end_direction * self.radius

            first_middle_angle = (
                start_angle
                + (end_angle - start_angle) * 0.33
            )

            second_middle_angle = (
                start_angle
                + (end_angle - start_angle) * 0.66
            )

            first_middle_direction = pygame.Vector2(1, 0).rotate(
                first_middle_angle
            )

            second_middle_direction = pygame.Vector2(1, 0).rotate(
                second_middle_angle
            )

            # Los puntos centrales se alejan del núcleo.
            first_middle = center + first_middle_direction * (
                self.radius + rng.uniform(1, 3)
            )

            second_middle = center + second_middle_direction * (
                self.radius + rng.uniform(2, 5)
            )

            points = [
                (int(start.x), int(start.y)),
                (int(first_middle.x), int(first_middle.y)),
                (int(second_middle.x), int(second_middle.y)),
                (int(end.x), int(end.y)),
            ]

            pygame.draw.lines(surface, (255, 225, 60), False, points, 2)
            pygame.draw.lines(surface, (255, 235, 235), False, points, 1)




BULLET_TYPES = {
    "normal": {
        "radius": config.BULLET_RADIUS,
        "damage": config.BULLET_DAMAGE,
        "rate": 1,
    },
    "gatling": {
        "radius": config.BULLET_RADIUS*0.75,
        "damage": config.BULLET_DAMAGE,
        "rate": 0.5,
    },
    "spread": {
        "radius": config.BULLET_RADIUS*1.5,
        "damage": config.BULLET_DAMAGE,
        "rate": 2,
    },
    "fragment": {
        "radius": max(1, int(config.BULLET_RADIUS * 0.6)),
        "damage": config.BULLET_DAMAGE,
        "rate": 1,
    },
}

ELEMENT_COLORS = {
    None: (218, 245, 244),
    "fire": (255, 137, 69),
    "ice": (64, 202, 255),
    "electric": (235, 214, 75),
    "poison": (180, 80, 220),
}




def build_bullet(x, y, vel_x, vel_y, max_dist, bullet_type, bullet_elements, effect_data, radius_multiplier=1.0):
    data = BULLET_TYPES[bullet_type]
    main_element = bullet_elements[0] if bullet_elements else None
    color = ELEMENT_COLORS[main_element]
    return Bullet(
        x=x,
        y=y,
        vel_x=vel_x,
        vel_y=vel_y,
        color=color,
        radius=max(1, round(data["radius"] * radius_multiplier),),
        damage=data["damage"],
        rate=data["rate"],
        max_distance=max_dist,
        elements = bullet_elements,
        effect_data=effect_data,
    )

def create_normal_shot(x, y, vel_x, vel_y, max_dist, elements, effect_data):
    bullet = build_bullet(x, y, vel_x, vel_y, max_dist, "normal", elements, effect_data)
    return [bullet], bullet.rate

def create_gatling_shot(x, y, vel_x, vel_y, max_dist, elements, effect_data):
    bullet = build_bullet(x, y, vel_x, vel_y, max_dist, "gatling", elements, effect_data)
    return [bullet], bullet.rate

def create_spread_shot(x, y, vel_x, vel_y, max_dist, elements, effect_data):
    bullets = []
    base_velocity = pygame.Vector2(vel_x, vel_y)
    
    total = 3
    angle_step = 12
    middle_index = (total - 1) / 2

    for index in range(total):
        angle = (index - middle_index) * angle_step
        rotated_velocity = base_velocity.rotate(angle)
        bullets.append(build_bullet(x, y, rotated_velocity.x, rotated_velocity.y, max_dist, "spread", elements, effect_data))

    return bullets, bullets[0].rate

def create_fragment(
    x,
    y,
    vel_x,
    vel_y,
    max_distance,
    damage,
    elements=None,
    effect_data=None,
    color=(235, 214, 75),
    fragment_style=None,
):
    fragment = Bullet(
        x=x,
        y=y,
        vel_x=vel_x,
        vel_y=vel_y,
        color=color,
        radius=BULLET_TYPES["fragment"]["radius"],
        damage=damage,
        rate=1,
        max_distance=max_distance,
        elements=elements or [],
        effect_data=effect_data or {},
        fragment_style=fragment_style,
    )

    fragment.can_fragment = False

    return fragment
