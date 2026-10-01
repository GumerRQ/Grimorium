""""Convierte room_data en habitaciones de verdad'"""

import pygame
import random

from game import config
from game.utils.paths import asset_path
from game.rooms.destructible import Destructible, Debris
from game.systems.impacts import Impact, apply_impact


class Room:
    def __init__(self, layout, room_type, viewport_width, viewport_height):
        self.layout = layout
        self.room_type = room_type
        self.cleared = False

        self.walls = []
        self.objects = []
        self.destructibles = []
        self.debris = []
        self.object_coins = 0
        self.voids = []
        self.floors = []
        self.floor_variants = {}
        self.doors = []

        self.player_spawn = None
        self.boss_spawn = None
        self.enemy_spawns = []
        self.trigger_spawns = []

        self.room_width = max(len(row) for row in self.layout) * config.ROOM_CELL_SIZE
        self.room_height = len(self.layout) * config.ROOM_CELL_SIZE

        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        self.room_width = max(len(row) for row in self.layout) * config.ROOM_CELL_SIZE
        self.room_height = len(self.layout) * config.ROOM_CELL_SIZE

        self.offset_x = (self.viewport_width - self.room_width) // 2
        self.offset_y = (self.viewport_height - self.room_height) // 2
       

        self.load_art()

        self.load_layout()
        self.build_tower_structure()
        


    def load_art(self):
        wall_top = pygame.image.load(
            asset_path("images", "tiles", "wall_top.png")
        ).convert_alpha()

        wall_top = pygame.transform.scale(
            wall_top,
            (config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE)
        )

        self.wall_sprites = {
            "top": wall_top,
            "bottom": pygame.transform.rotate(wall_top, 180),
            "left": pygame.transform.rotate(wall_top, 90),
            "right": pygame.transform.rotate(wall_top, -90),
        }

        self.corners = []
        self.corner_keys = set()

        outer_top_right = pygame.image.load(
            asset_path("images", "tiles", "outer_top_right.png")
        ).convert_alpha()
        outer_top_right = pygame.transform.scale(
            outer_top_right,
            (config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE)
        )

        inner_bottom_right = pygame.image.load(
            asset_path("images", "tiles", "inner_bottom_right.png")
        ).convert_alpha()
        inner_bottom_right = pygame.transform.scale(
            inner_bottom_right,
            (config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE)
        )

        self.corner_sprites = {
            "outer_top_right": outer_top_right,
            "outer_top_left": pygame.transform.flip(outer_top_right, True, False),
            "outer_bottom_right": pygame.transform.flip(outer_top_right, False, True),
            "outer_bottom_left": pygame.transform.flip(outer_top_right, True, True),

            "inner_bottom_right": inner_bottom_right,
            "inner_bottom_left": pygame.transform.flip(inner_bottom_right, True, False),
            "inner_top_right": pygame.transform.flip(inner_bottom_right, False, True),
            "inner_top_left": pygame.transform.flip(inner_bottom_right, True, True),
        }

        self.floor_sprites = self.load_floor_sprites()
        self.floor_shadow_overlays = self.create_floor_shadow_overlays()

        self.common_floor_indices = [4, 5]
        self.used_rare_floor_indices = set()
        self.used_rare_floor_positions = []
        
        door_closed_left_top = pygame.image.load(
            asset_path("images", "tiles", "door_closed_left_top.png")
        ).convert_alpha()

        door_closed_left_top = pygame.transform.scale(
            door_closed_left_top,
            (config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE)
        )

        door_open_left_top = pygame.image.load(
            asset_path("images", "tiles", "door_open_left_top.png")
        ).convert_alpha()

        door_open_left_top = pygame.transform.scale(
            door_open_left_top,
            (config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE)
        )

        door_closed_right_top = pygame.transform.flip(
            door_closed_left_top,
            True,
            False,
        )

        door_open_right_top = pygame.transform.flip(
            door_open_left_top,
            True,
            False,
        )

        self.door_sprites = {
            "closed": {
                "top": {
                    "left": door_closed_left_top,
                    "right": door_closed_right_top,
                },
                "bottom": {
                    "left": pygame.transform.rotate(door_closed_right_top, 180),
                    "right": pygame.transform.rotate(door_closed_left_top, 180),
                },
            },
            "open": {
                "top": {
                    "left": door_open_left_top,
                    "right": door_open_right_top,
                },
                "bottom": {
                    "left": pygame.transform.rotate(door_open_right_top, 180),
                    "right": pygame.transform.rotate(door_open_left_top, 180),
                },
            },
        }

    def is_floor_tile(self, row, col):
        if row < 0 or row >= len(self.layout):
            return False

        if col < 0 or col >= len(self.layout[row]):
            return False

        tile = self.layout[row][col]

        return tile in [".", "P", "B", "E", "O", "N", "V", "I"]
    
    def choose_floor_sprite(self, row, col):
        rare_indices = [
            index
            for index in range(len(self.floor_sprites))
            if index not in self.common_floor_indices
            and index not in self.used_rare_floor_indices
        ]

        choices = self.common_floor_indices + rare_indices
        weights = [8, 8]

        for _index in rare_indices:
            weight = 1

            for rare_row, rare_col in self.used_rare_floor_positions:
                distance = abs(row - rare_row) + abs(col - rare_col)

                if distance == 1:
                    weight *= 0.05
                elif distance == 2:
                    weight *= 0.25

            weights.append(weight)

        index = random.choices(choices, weights=weights, k=1)[0]

        if index not in self.common_floor_indices:
            self.used_rare_floor_indices.add(index)
            self.used_rare_floor_positions.append((row, col))

        sprite = self.floor_sprites[index]
        self._last_floor_transform = (0, False, False)

        if index in self.common_floor_indices:
            sprite = self.randomize_floor_sprite(sprite)

        self.floor_variants[(row, col)] = (index, *self._last_floor_transform)

        return sprite
    
    def get_door_side(self, row, col):
        if self.is_floor_tile(row + 1, col):
            return "top"

        if self.is_floor_tile(row - 1, col):
            return "bottom"

        if self.is_floor_tile(row, col + 1):
            return "left"

        if self.is_floor_tile(row, col - 1):
            return "right"

        return "top"


    def load_layout(self):
        for row_index, row in enumerate(self.layout):
            for col_index, tile in enumerate(row):
                x = self.offset_x + col_index * config.ROOM_CELL_SIZE 
                y = self.offset_y + row_index * config.ROOM_CELL_SIZE 

                rect = pygame.Rect(x, y, config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE )

                tile = self.layout[row_index][col_index]

                if tile == "D":
                    self.add_double_door(rect, row_index, col_index, "exit", starts_open=False)
                    continue

                if tile == "A":
                    self.add_double_door(rect, row_index, col_index, "entrance", starts_open=True)
                    continue

                if tile in ["d", "a"]:
                    continue

                if not self.is_floor_tile(row_index, col_index):
                    continue

                self.floors.append({
                    "rect": rect,
                    "row": row_index,
                    "col": col_index,
                    "sprite": None,
                    "shadow_sides": self.get_floor_shadow_sides(row_index, col_index),
                })

                self.detect_corners_for_tile(row_index, col_index, x, y)

                tile = self.layout[row_index][col_index]

                if tile == "P":
                    self.player_spawn = (x + config.ROOM_CELL_SIZE //2, y + config.ROOM_CELL_SIZE //2)

                elif tile == "B":
                    self.boss_spawn = (x + config.ROOM_CELL_SIZE //2, y + config.ROOM_CELL_SIZE//2)

                elif tile == "E":
                    enemy = (x + config.ROOM_CELL_SIZE //2, y + config.ROOM_CELL_SIZE //2)
                    self.enemy_spawns.append(enemy)

                elif tile == "O":
                    prop = Destructible(rect, on_destroy=self.destroy_object)
                    self.destructibles.append(prop)
                    self.objects.append(prop.rect)

                elif tile == "V":
                    self.voids.append(rect)

                elif tile == "N":
                    self.trigger_spawns.append(rect)

                        
                if not self.is_floor_tile(row_index - 1, col_index) and not self.is_door_tile(row_index - 1, col_index):
                    self.add_wall(pygame.Rect(x, y - config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE),
                                  "top")

                if not self.is_floor_tile(row_index + 1, col_index) and not self.is_door_tile(row_index + 1, col_index):
                    self.add_wall(pygame.Rect(x, y + config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE),
                                  "bottom")

                if not self.is_floor_tile(row_index, col_index - 1) and not self.is_door_tile(row_index, col_index - 1):
                    self.add_wall(pygame.Rect(x - config.ROOM_CELL_SIZE, y, config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE),
                                  "left")

                if not self.is_floor_tile(row_index, col_index + 1) and not self.is_door_tile(row_index, col_index + 1):
                    self.add_wall(pygame.Rect(x + config.ROOM_CELL_SIZE, y, config.ROOM_CELL_SIZE, config.ROOM_CELL_SIZE),
                                  "right")

        self.assign_floor_sprites()

    
    def close_entrance_doors(self):
        for door in self.doors:
            if door["type"] == "entrance":
                door["open"] = False

    
    def open_doors(self):
        for door in self.doors:
            if door["type"] == "exit":
                door["open"] = True


    def get_entrance_door(self):
        for door in self.doors:
            if door["type"] == "entrance":
                return door

        return None

    
    def add_double_door(self, rect, row, col, door_type, starts_open=False):
        side = self.get_door_side(row, col)

        second_rect = rect.copy()

        if side in ["top", "bottom"]:
            second_rect.x += config.ROOM_CELL_SIZE
        else:
            second_rect.y += config.ROOM_CELL_SIZE

        full_rect = rect.union(second_rect)
        trigger_rect = self.get_double_door_trigger_rect(full_rect, row, col, side)

        if door_type == "exit":
            self.trigger_spawns.append(trigger_rect)

        self.doors.append({
            "rects": [rect, second_rect],
            "block_rects": [
                self.get_door_block_rect(rect, side),
                self.get_door_block_rect(second_rect, side),
            ],
            "full_rect": full_rect,
            "trigger_rect": trigger_rect,
            "side": side,
            "type": door_type,
            "open": starts_open,
        })

    def get_double_door_trigger_rect(self, full_rect, row, col, side):
        trigger_size = config.ROOM_CELL_SIZE // 0.75

        trigger_rect = pygame.Rect(0, 0, trigger_size, trigger_size)
        trigger_rect.center = full_rect.center

        enter_depth = config.ROOM_CELL_SIZE // 0.75

        if side == "top":
            trigger_rect.centery = full_rect.bottom - enter_depth

        elif side == "bottom":
            trigger_rect.centery = full_rect.top + enter_depth

        elif side == "left":
            trigger_rect.centerx = full_rect.right - enter_depth

        elif side == "right":
            trigger_rect.centerx = full_rect.left + enter_depth

        return trigger_rect 

    def assign_floor_sprites(self):
        floors = self.floors.copy()
        random.shuffle(floors)

        for floor in floors:
            floor["sprite"] = self.choose_floor_sprite(
                floor["row"],
                floor["col"],
            )

    def randomize_floor_sprite(self, sprite):
        rotations = [0, 90, 180, 270]
        angle = random.choice(rotations)

        result = pygame.transform.rotate(sprite, angle)

        flip_x = random.choice([False, True])
        flip_y = random.choice([False, True])
        self._last_floor_transform = (angle, flip_x, flip_y)

        if flip_x or flip_y:
            result = pygame.transform.flip(result, flip_x, flip_y)

        return result


    def add_wall(self, rect, side):
        self.walls.append({
            "rect": rect,
            "side": side,
        })

    
    def add_corner(self, x, y, corner_type):
        key = (x, y, corner_type)

        if key in self.corner_keys:
            return

        self.corner_keys.add(key)
        self.corners.append({
            "x": x,
            "y": y,
            "type": corner_type,
        })

    
    def detect_corners_for_tile(self, row, col, x, y):
        tile_size = config.ROOM_CELL_SIZE

        up = self.is_floor_tile(row - 1, col)
        down = self.is_floor_tile(row + 1, col)
        left = self.is_floor_tile(row, col - 1)
        right = self.is_floor_tile(row, col + 1)

        up_left = self.is_floor_tile(row - 1, col - 1)
        up_right = self.is_floor_tile(row - 1, col + 1)
        down_left = self.is_floor_tile(row + 1, col - 1)
        down_right = self.is_floor_tile(row + 1, col + 1)

        if not up and not left:
            self.add_corner(x - tile_size, y - tile_size, "outer_top_left")

        if not up and not right:
            self.add_corner(x + tile_size, y - tile_size, "outer_top_right")

        if not down and not left:
            self.add_corner(x - tile_size, y + tile_size, "outer_bottom_left")

        if not down and not right:
            self.add_corner(x + tile_size, y + tile_size, "outer_bottom_right")

        if up and left and not up_left:
            self.add_corner(x - tile_size, y - tile_size, "inner_bottom_right")

        if up and right and not up_right:
            self.add_corner(x + tile_size, y - tile_size, "inner_bottom_left")

        if down and left and not down_left:
            self.add_corner(x - tile_size, y + tile_size, "inner_top_right")

        if down and right and not down_right:
            self.add_corner(x + tile_size, y + tile_size, "inner_top_left")


    def hit_object(self, prop, body=False, impact=None):
        if prop not in self.destructibles:
            return
        return apply_impact(prop, impact or Impact(kind='contact' if body else 'projectile'))

    def destroy_object(self, prop):
        if prop not in self.destructibles:
            return
        self.destructibles.remove(prop)
        self.objects.remove(prop.rect)
        self.debris.extend(Debris(image, prop.rect.center) for image in prop.fragments)
        self.object_coins += prop.spec['coins']

    def update_objects(self, dt):
        for prop in self.destructibles:
            prop.update(dt)
        for fragment in self.debris:
            fragment.update(dt, self)

    def get_blocking_rects(self, include_walls=True, include_objects=True, include_voids=False):
        rects = []

        if include_walls:
            rects.extend(wall["rect"] for wall in self.walls)

            for door in self.doors:
                if door["open"]:
                    continue

                rects.extend(door["block_rects"])

        if include_objects:
            rects.extend(self.objects)

        if include_voids:
            rects.extend(self.voids)

        return rects

    
    def is_door_tile(self, row, col):
        if row < 0 or row >= len(self.layout):
            return False

        if col < 0 or col >= len(self.layout[row]):
            return False

        return self.layout[row][col] in ["D", "d", "A", "a"]
    

    def get_door_block_rect(self, rect, side):
        block_rect = rect.copy()
        inset = config.ROOM_CELL_SIZE // 2

        if side == "top":
            block_rect.height = inset
            block_rect.top = rect.top

        elif side == "bottom":
            block_rect.height = inset
            block_rect.bottom = rect.bottom

        elif side == "left":
            block_rect.width = inset
            block_rect.left = rect.left

        elif side == "right":
            block_rect.width = inset
            block_rect.right = rect.right

        return block_rect
    

    def world_to_cell(self, x, y):
        col = int((x - self.offset_x) // config.ROOM_CELL_SIZE)
        row = int((y - self.offset_y) // config.ROOM_CELL_SIZE)
        return row, col

    def cell_to_world(self, row, col):
        x = self.offset_x + col * config.ROOM_CELL_SIZE + config.ROOM_CELL_SIZE // 2
        y = self.offset_y + row * config.ROOM_CELL_SIZE + config.ROOM_CELL_SIZE // 2
        return x, y

    def is_walkable_cell(self, row, col):
        if row < 0 or row >= len(self.layout):
            return False

        if col < 0 or col >= len(self.layout[row]):
            return False

        tile = self.layout[row][col]

        return tile in [".", "P", "B", "E", "N", "I"]
    

    def load_floor_sprites(self):
        sheet = pygame.image.load(
            asset_path("images", "tiles", "floor_tiles.bmp")
        ).convert_alpha()

        sprites = []
        tile_size = config.ROOM_CELL_SIZE

        for row in range(3):
            for col in range(3):
                rect = pygame.Rect(
                    col * tile_size,
                    row * tile_size,
                    tile_size,
                    tile_size,
                )

                sprite = sheet.subsurface(rect).copy()
                sprites.append(sprite)

        return sprites
    

    def create_floor_shadow_overlays(self):
        tile_size = config.ROOM_CELL_SIZE
        shadow_size = 5
        max_alpha = 150

        overlays = {
            "top": pygame.Surface((tile_size, tile_size), pygame.SRCALPHA),
            "bottom": pygame.Surface((tile_size, tile_size), pygame.SRCALPHA),
            "left": pygame.Surface((tile_size, tile_size), pygame.SRCALPHA),
            "right": pygame.Surface((tile_size, tile_size), pygame.SRCALPHA),
            "top_left": pygame.Surface((tile_size, tile_size), pygame.SRCALPHA),
            "top_right": pygame.Surface((tile_size, tile_size), pygame.SRCALPHA),
            "bottom_left": pygame.Surface((tile_size, tile_size), pygame.SRCALPHA),
            "bottom_right": pygame.Surface((tile_size, tile_size), pygame.SRCALPHA),
        }

        for i in range(shadow_size):
            alpha = int(max_alpha * (1 - i / shadow_size))

            pygame.draw.line(
                overlays["top"],
                (0, 0, 0, alpha),
                (0, i),
                (tile_size - 1, i),
            )
            pygame.draw.line(
                overlays["bottom"],
                (0, 0, 0, alpha),
                (0, tile_size - 1 - i),
                (tile_size - 1, tile_size - 1 - i),
            )
            pygame.draw.line(
                overlays["left"],
                (0, 0, 0, alpha),
                (i, 0),
                (i, tile_size - 1),
            )
            pygame.draw.line(
                overlays["right"],
                (0, 0, 0, alpha),
                (tile_size - 1 - i, 0),
                (tile_size - 1 - i, tile_size - 1),
            )

        for i in range(shadow_size):
            for j in range(shadow_size):
                distance = max(i, j)
                alpha = int(max_alpha * (1 - distance / shadow_size))

                overlays["top_left"].set_at(
                    (i, j),
                    (0, 0, 0, alpha),
                )
                overlays["top_right"].set_at(
                    (tile_size - 1 - i, j),
                    (0, 0, 0, alpha),
                )
                overlays["bottom_left"].set_at(
                    (i, tile_size - 1 - j),
                    (0, 0, 0, alpha),
                )
                overlays["bottom_right"].set_at(
                    (tile_size - 1 - i, tile_size - 1 - j),
                    (0, 0, 0, alpha),
                )

        return overlays
    

    def get_floor_shadow_sides(self, row, col):
        sides = []

        up = self.is_floor_tile(row - 1, col)
        down = self.is_floor_tile(row + 1, col)
        left = self.is_floor_tile(row, col - 1)
        right = self.is_floor_tile(row, col + 1)

        up_left = self.is_floor_tile(row - 1, col - 1)
        up_right = self.is_floor_tile(row - 1, col + 1)
        down_left = self.is_floor_tile(row + 1, col - 1)
        down_right = self.is_floor_tile(row + 1, col + 1)

        if not up:
            sides.append("top")
        if not down:
            sides.append("bottom")
        if not left:
            sides.append("left")
        if not right:
            sides.append("right")

        if up and left and not up_left:
            sides.append("top_left")
        if up and right and not up_right:
            sides.append("top_right")
        if down and left and not down_left:
            sides.append("bottom_left")
        if down and right and not down_right:
            sides.append("bottom_right")

        return sides


    def build_tower_structure(self):
        """Unseen space inside the shared footprint, with no extra architecture."""
        cell = config.ROOM_CELL_SIZE
        self.perimeter_rect = pygame.Rect(self.offset_x - cell, self.offset_y + cell,
                                         15 * cell, 10 * cell)
        self.structure = pygame.Surface((self.viewport_width, self.viewport_height), pygame.SRCALPHA)
        # Lower floors are supplied by the run history; no invented black slab.

    def draw(self, surface, include_structure=True):
        if include_structure:
            surface.blit(self.structure, (0, 0))
        for floor in self.floors:
            surface.blit(floor["sprite"], floor["rect"].topleft)

            for side in floor["shadow_sides"]:
                surface.blit(
                    self.floor_shadow_overlays[side],
                    floor["rect"].topleft,
                )
                
        for fragment in self.debris:
            fragment.draw(surface)
        for prop in self.destructibles:
            prop.draw(surface)

        for void in self.voids:
            pygame.draw.rect(surface, (5, 5, 10), void)

        for wall in self.walls:
            sprite = self.wall_sprites[wall["side"]]
            surface.blit(sprite, wall["rect"].topleft)

        for door in self.doors:
            state = "open" if door["open"] else "closed"

            left_sprite = self.door_sprites[state][door["side"]]["left"]
            right_sprite = self.door_sprites[state][door["side"]]["right"]

            surface.blit(left_sprite, door["rects"][0].topleft)
            surface.blit(right_sprite, door["rects"][1].topleft)

        for corner in self.corners:
            sprite = self.corner_sprites[corner["type"]]
            surface.blit(sprite, (corner["x"], corner["y"]))
