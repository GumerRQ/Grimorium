import re
import pygame
import random

from game import config
from game.ui.fonts import create_font
from game.screens.base_screen import BaseScreen
from game.systems.shop_effects import apply_potion, apply_book, apply_power

from game.utils.paths import asset_path

PLUS_BORDER_STYLE = "pulse"
PLUS_BORDER_PULSE_STEP_MS = 110
PLUS_BORDER_SWEEP_STEP_MS = 30
PLUS_BORDER_SWEEP_COOLDOWN_MS = 1200
PLUS_TEXT_SHINE_DURATION_MS = 1800
PLUS_BORDER_GOLD_COLORS = [
    (170, 92, 12), (175, 96, 13), (180, 101, 14),
    (186, 107, 16), (192, 114, 18), (199, 121, 20),
    (206, 129, 23), (199, 121, 20), (192, 114, 18), 
    (186, 107, 16), (180, 101, 14), (175, 96, 13),
]
PLUS_BORDER_SWEEP_COLORS = [
    (219, 140, 30),
    (232, 160, 48),
    (243, 185, 72),
    (232, 160, 48),
    (219, 140, 30),
]

class ShopScreen(BaseScreen):
    CAN_PAUSE = True
    VIRTUAL_WIDTH = 320
    VIRTUAL_HEIGHT = 180
    def __init__(self, game):
        super().__init__(game)
        self.player = self.game.run_state.player

        self.background = pygame.image.load(asset_path("images", "shop.bmp")).convert()
        self.background_original_size = self.background.get_size()

        self.base_width, self.base_height = self.background_original_size

        self.pixel_scale = min(
            self.VIRTUAL_WIDTH // self.base_width,
            self.VIRTUAL_HEIGHT // self.base_height,
        )

        self.player.visual.set_fixed_frame(0, 2)
        self.player.visual.set_size(32 * self.pixel_scale, 32 * self.pixel_scale)

        self.render_width = self.base_width * self.pixel_scale
        self.render_height = self.base_height * self.pixel_scale
        self.offset_x = (self.VIRTUAL_WIDTH - self.render_width) // 2
        self.offset_y = (self.VIRTUAL_HEIGHT - self.render_height) // 2

        self.background = pygame.transform.scale(
            self.background,
            (self.render_width, self.render_height),
        )

        self.title_font = create_font(pixel_scale=self.pixel_scale)
        self.info_font = create_font(pixel_scale=self.pixel_scale)
        self.tooltip_font = self.info_font
        self.unlabeled_background = self.background.copy()
        self.tooltip_icon_w = 5
        self.tooltip_icon_h = 6
        self.tooltip_icons = self.load_tooltip_icons()

        self.player.x = self.offset_x + 205 * self.pixel_scale
        self.player.y = self.offset_y + 124 * self.pixel_scale

        self.shop_slots = {
            "potions": [
                (129, 51), (149, 51), (169, 51), (189, 51),
                (129, 84), (149, 84), (169, 84), (189, 84),
            ],
            "books": [
                (232, 45), (264, 45),
                (232, 67), (264, 67),
                (232, 89), (264, 89),
            ],
            "powers": [
                (55, 49), (87, 49),
                (55, 84), (87, 84),
            ],
        }

        item_size = (32 * self.pixel_scale, 32 * self.pixel_scale)

        self.loaded_potions = self.load_shop_assets(
            config.POTION_DATA,
            (0, 0, 0),
            item_size,
        )
        self.potions_in_shop = self.build_shop_items(
            self.loaded_potions,
            self.shop_slots["potions"],
            config.POTION_DATA,
            max_items = 4,
        )

        self.loaded_books = self.load_shop_assets(
            config.BOOK_DATA,
            (0, 147, 71),
            item_size,
        )
        self.books_in_shop = self.build_shop_items(
            self.loaded_books,
            self.shop_slots["books"],
            config.BOOK_DATA,
            self.can_book_appear,
            max_items = 3,
        )

        self.loaded_powers = self.load_shop_assets(
            config.POWER_DATA,
            (0, 147, 0),
            item_size,
        )
        self.powers_in_shop = self.build_shop_items(
            self.loaded_powers,
            self.shop_slots["powers"],
            config.POWER_DATA,
            self.can_power_appear,
            allow_duplicates=False,
            max_items = 4,
        )

        self.price_images = self.load_price_images()

        self.price_positions = {
            "powers": (70, 105),
            "potions": (158, 105),
            "books": (248, 105),
        }

        self.stat_positions = {
            "coins": (208, 144),
            "health": (177, 117),
            "damage": (177, 124),
            "speed": (177, 132),
            "fire_rate": (241, 117),
            "shoot_distance": (241, 124),
            "body_damage": (241, 132),
            "luck": (0, 0),
        }

        self.scaled_stat_positions = {
            key: self.scale_layout_point(point)
            for key, point in self.stat_positions.items()
        }

        self.level_book_images = self.load_level_book_images()

        self.power_levels_book_size = (146, 68)

        power_levels_book_original = pygame.image.load(
            asset_path("images", "ui", "power_levels_book.png")
        ).convert_alpha()

        self.unlabeled_book = power_levels_book_original.copy()
        self.refresh_language()

        # Libro centrado horizontalmente.
        self.power_levels_book_x = 141

        # Abierto: 112 + 68 = 180.
        self.power_levels_book_open_y = 112

        # Cerrado: quedan visibles 20 pÃ­xeles.
        self.power_levels_book_closed_y = 155

        self.power_levels_book_y = float(
            self.power_levels_book_closed_y
        )

        self.power_levels_book_speed = 10.0


        self.power_level_positions = [
            # PÃ¡gina izquierda.
            (15, 28),
            (44, 28),
            (15, 40),
            (44, 40),
            (15, 52),
            (44, 52),

            # PÃ¡gina derecha.
            (78, 28),
            (107, 28),
            (78, 40),
            (107, 40),
            (78, 52),
            (107, 52),
        ]

        self.power_level_hitboxes = []

        self.keyboard_mode = True
        self.focus_index = 0
        self.level_book_pinned = False
        self.notice = ""
        self.notice_time = 0.0
        self.levels_button = pygame.Rect(6, 151, 65, 10)
        self.leave_button = pygame.Rect(6, 163, 65, 10)
        self.focus_age = 0.0
        self.focus_signature = None


    def on_enter(self):
        if self.art_language != self.game.localization.language:
            self.refresh_language()

    def refresh_language(self):
        self.art_language = self.game.localization.language
        self.background = self.unlabeled_background.copy()
        # Replace lettering on the loaded copy, keeping the editable art intact.
        for key, x, width, sample_x in (("powers", 53, 36, 50),
                                       ("potions", 140, 38, 137),
                                       ("books", 234, 30, 230)):
            scale = self.pixel_scale
            color = self.background.get_at((sample_x * scale, 22 * scale))
            rect = pygame.Rect(x * scale, 18 * scale, width * scale, 9 * scale)
            self.background.fill(color, rect)
            label = self.title_font.render(self.game.localization.text(f"ui.shop.{key}"),
                                           True, (30, 24, 17))
            self.background.blit(label, label.get_rect(center=rect.center))
        power_levels_book_original = self.unlabeled_book.copy()
        page_color = power_levels_book_original.get_at((35, 30))
        power_levels_book_original.fill(page_color, (14, 8, 55, 16))
        label = create_font(pixel_scale=1).render(
            self.game.localization.text("ui.shop.spells"), True, (82, 53, 32))
        power_levels_book_original.blit(label, label.get_rect(center=(41, 16)))

        self.power_levels_book = pygame.transform.scale(
            power_levels_book_original,
            (
                self.power_levels_book_size[0] * self.pixel_scale,
                self.power_levels_book_size[1] * self.pixel_scale,
            ),
        )


    def load_shop_assets(self, item_data, colorkey, size):
        loaded_items = []

        for item_id, data in item_data.items():
            image_path = asset_path(*data["asset"].split("/"))

            image = pygame.image.load(str(image_path)).convert_alpha()
            image.set_colorkey(colorkey)
            image = pygame.transform.scale(image, size).convert_alpha()

            loaded_items.append({
                "id": item_id,
                "image": image,
                "path": str(image_path),
            })

        return loaded_items
    

    def build_shop_items(self, loaded_items, slots, price_data, can_appear=None, allow_duplicates=True, max_items=None):
        shop_items = []

        available_items = []

        for item in loaded_items:
            item_id = item["id"]

            if item_id not in price_data:
                continue

            if can_appear is not None and not can_appear(item_id):
                continue

            available_items.append(item)

        if not available_items:
            return shop_items
        
        slot_count = len(slots)

        if max_items is not None:
            slot_count = min(slot_count, max_items)

        if allow_duplicates:
            items_to_show = []
            selectable_items = available_items.copy()

            while selectable_items and len(items_to_show) < slot_count:
                selected_item = random.choice(selectable_items)
                items_to_show.append(selected_item)

                selected_id = selected_item["id"]
                selected_data = price_data[selected_id]

                if selected_data.get("is_plus", False):
                    selectable_items.remove(selected_item)
        else:
            items_to_show = random.sample(
                available_items,
                min(len(slots), len(available_items)),
            )

        slots_to_use = random.sample(slots, len(items_to_show))

        for slot, item_data in zip(slots_to_use, items_to_show):
            rect = self.build_layout_rect(slot, (32, 32))
            image = item_data["image"]
            visible = image.get_bounding_rect(min_alpha=1)

            shop_items.append({
                "id": item_data["id"],
                "image": item_data["image"],
                "price": price_data[item_data["id"]]["price"],
                "rect": rect,
                "hit_rect": visible.move(rect.topleft).inflate(4, 4),
            })

        return shop_items


    def load_price_image(self, price):
        image = pygame.image.load(
            asset_path("images", "prices", f"price_{price}.png")
        ).convert_alpha()

        return pygame.transform.scale(
            image,
            (19 * self.pixel_scale, 11 * self.pixel_scale),
        )


    def load_price_images(self):
        return {
            "powers": self.load_price_image(config.POWER_PRICE),
            "potions": self.load_price_image(config.POTION_PRICE),
            "books": self.load_price_image(config.BOOK_PRICE),
        }
    
    def load_level_book_images(self):
        images = {}

        for image_path in asset_path("images", "level_books").glob("*.png"):
            level_id = image_path.stem

            image = pygame.image.load(str(image_path)).convert_alpha()
            image = pygame.transform.scale(
                image,
                (25 * self.pixel_scale, 10 * self.pixel_scale),
            )

            images[level_id] = image

        return images
    

    def buy_item(self, item, items, apply_function):
        result = self.game.run_state.purchase(item, items, apply_function)
        if result == 'poor':
            self.notice, self.notice_time = "ui.shop.poor", 2.0
        elif result == 'bought':
            self.notice, self.notice_time = "ui.shop.bought", 1.2

    def buy_potion(self, potion):
        self.buy_item(potion, self.potions_in_shop, apply_potion)


    def buy_book(self, book):
        self.buy_item(book, self.books_in_shop, apply_book)


    def buy_power(self, power):
        self.buy_item(power, self.powers_in_shop, apply_power)

    
    def get_owned_power_elements(self):
        owned = set(self.player.base_bullet_elements)
        owned.update(self.player.extra_bullet_element.keys())
        return owned


    def can_power_appear(self, power_id):
        power_data = config.POWER_DATA[power_id]
        category = power_data.get("category", "element")

        if category == "shot_modifier":
            return power_id not in self.player.shot_modifiers

        owned_elements = self.get_owned_power_elements()
        return power_data["element"] not in owned_elements
    

    def can_book_appear(self, book_id):
        book_data = config.BOOK_DATA[book_id]
        effect = book_data["effect"]
        owned_elements = self.get_owned_power_elements()

        if book_data.get("is_plus", False):
            if self.player.books_purchased < config.PLUS_BOOK_MIN_PURCHASED_BOOKS:
                return False

            if book_id in self.player.purchased_books:
                return False

            if random.random() >= config.PLUS_BOOK_APPEAR_CHANCE:
                return False

        if "element" in effect:
            return effect["element"] in owned_elements

        if "combo" in effect:
            combo_elements = set(effect["combo"].split("_"))
            return combo_elements.issubset(owned_elements)

        return False
    
    def get_power_levels_book_rect(self):
        x = (
            self.offset_x
            + self.power_levels_book_x * self.pixel_scale
        )

        y = (
            self.offset_y
            + int(self.power_levels_book_y) * self.pixel_scale
        )

        return self.power_levels_book.get_rect(topleft=(x, y))
    
    def update(self, dt):
        self.notice_time = max(0, self.notice_time - dt)
        if self.keyboard_mode:
            kind, item, _ = self.keyboard_targets()[self.focus_index]
            signature = (self.focus_index, kind, item["id"] if item else None)
            if signature != self.focus_signature:
                self.focus_signature = signature
                self.focus_age = 0.0
            else:
                self.focus_age += dt
        mouse_pos = self.screen_to_virtual(pygame.mouse.get_pos())
        book_rect = self.get_power_levels_book_rect()

        if self.level_book_pinned or (not self.keyboard_mode and book_rect.collidepoint(mouse_pos)):
            target_y = self.power_levels_book_open_y
        else:
            target_y = self.power_levels_book_closed_y

        animation_amount = min(
            1.0,
            self.power_levels_book_speed * dt,
        )

        self.power_levels_book_y += (
            target_y - self.power_levels_book_y
        ) * animation_amount

        if abs(self.power_levels_book_y - target_y) < 0.1:
            self.power_levels_book_y = float(target_y)

    def keyboard_targets(self):
        targets = []
        for kind, items in (("potion", self.potions_in_shop),
                            ("power", self.powers_in_shop), ("book", self.books_in_shop)):
            targets.extend((kind, item, item["hit_rect"]) for item in items)
        targets.sort(key=lambda target: (target[2].centery, target[2].centerx))
        targets.append(("levels", None, self.levels_button))
        if self.level_book_pinned:
            book = self.get_power_levels_book_rect()
            for level_id, (x, y) in zip(self.get_visible_power_level_ids(), self.power_level_positions):
                rect = self.level_book_images[f"lvl_{level_id}"].get_rect(
                    topleft=(book.x + x * self.pixel_scale, book.y + y * self.pixel_scale))
                targets.append(("level", {"id": level_id, "rect": rect}, rect))
        targets.append(("leave", None, self.leave_button))
        self.focus_index = min(self.focus_index, len(targets) - 1)
        return targets

    def move_focus(self, dx, dy):
        targets = self.keyboard_targets()
        origin = pygame.Vector2(targets[self.focus_index][2].center)
        candidates = []
        for index, (_, _, rect) in enumerate(targets):
            delta = pygame.Vector2(rect.center) - origin
            forward = delta.x * dx + delta.y * dy
            if forward > 1:
                cross = abs(delta.x * dy - delta.y * dx)
                candidates.append((forward + cross * 2, index))
        if candidates:
            self.focus_index = min(candidates)[1]

    def perform_action(self, kind, item=None):
        if self.game.screen_manager.current_screen is not self or getattr(self, '_transitioned', False):
            return
        self.focus_age = 0.0
        if kind == "leave":
            self.game.finish_current_screen(self)
        elif kind == "levels":
            self.level_book_pinned = not self.level_book_pinned
        elif kind in ("potion", "power", "book"):
            {"potion": self.buy_potion, "power": self.buy_power, "book": self.buy_book}[kind](item)
            self.keyboard_targets()
        # A level entry is an informational tooltip, not an equipment slot.

    def activate_focus(self):
        kind, item, _ = self.keyboard_targets()[self.focus_index]
        self.perform_action(kind, item)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.keyboard_mode = True
            directions = {pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
                          pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
                          pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
                          pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1)}
            if event.key in directions:
                self.move_focus(*directions[event.key])
            elif event.key == pygame.K_TAB:
                count = len(self.keyboard_targets())
                self.focus_index = (self.focus_index + (-1 if event.mod & pygame.KMOD_SHIFT else 1)) % count
            elif event.key in (pygame.K_e, pygame.K_SPACE):
                if not getattr(event, "repeat", False):
                    if self.keyboard_targets()[self.focus_index][0] != "leave":
                        self.activate_focus()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if not getattr(event, "repeat", False):
                    self.perform_action("leave")
            elif event.key == pygame.K_i:
                if getattr(event, "repeat", False):
                    return
                self.perform_action("levels")
                targets = self.keyboard_targets()
                self.focus_index = next((i for i, t in enumerate(targets) if t[0] == "level"),
                                        next(i for i, t in enumerate(targets) if t[0] == "levels"))
            return

        if event.type == pygame.MOUSEMOTION and event.rel != (0, 0):
            self.keyboard_mode = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.keyboard_mode = False
            mouse_pos = self.screen_to_virtual(event.pos)
            for kind, item, rect in reversed(self.keyboard_targets()):
                if rect.collidepoint(mouse_pos):
                    self.perform_action(kind, item)
                    return

    def screen_to_virtual(self, pos):
        return super().screen_to_virtual(pos)

    def draw_shop_items(self, surface):
        for item in self.potions_in_shop + self.books_in_shop + self.powers_in_shop:
            surface.blit(item["image"], item["rect"])

    
    def draw_prices(self, surface):
        for key, image in self.price_images.items():
            rect = image.get_rect(
                center=self.scale_layout_point(self.price_positions[key])
            )
            surface.blit(image, rect)
    
   
    def get_level_texts(self):
        return {
            "fire": self.game.localization.text("ui.shop.level") + f"{self.player.element_stats['fire']['level']}",
            "ice": self.game.localization.text("ui.shop.level") + f"{self.player.element_stats['ice']['level']}",
            "electric": self.game.localization.text("ui.shop.level") + f"{self.player.element_stats['electric']['level']}",
            "poison": self.game.localization.text("ui.shop.level") + f"{self.player.element_stats['poison']['level']}",

            "fire_ice": self.game.localization.text("ui.shop.level") + f"{self.player.combo_stats['fire_ice']['level']}",
            "fire_electric": self.game.localization.text("ui.shop.level") + f"{self.player.combo_stats['fire_electric']['level']}",
            "ice_electric": self.game.localization.text("ui.shop.level") + f"{self.player.combo_stats['ice_electric']['level']}",
            "fire_poison": self.game.localization.text("ui.shop.level") + f"{self.player.combo_stats['fire_poison']['level']}",
            "ice_poison": self.game.localization.text("ui.shop.level") + f"{self.player.combo_stats['ice_poison']['level']}",
            "electric_poison": self.game.localization.text("ui.shop.level") + f"{self.player.combo_stats['electric_poison']['level']}",
        }
    

    def get_visible_power_level_ids(self):
        visible_levels = []

        ordered_elements = self.player.power_element_order.copy()

        configured_elements = (
            self.player.base_bullet_elements
            + list(self.player.extra_bullet_element.keys())
        )

        for element in configured_elements:
            if element not in ordered_elements:
                ordered_elements.append(element)

        previous_elements = []

        for element in ordered_elements:
            visible_levels.append(element)

            for previous_element in previous_elements:
                combo_forward = f"{previous_element}_{element}"
                combo_reverse = f"{element}_{previous_element}"

                if combo_forward in self.player.combo_stats:
                    visible_levels.append(combo_forward)
                elif combo_reverse in self.player.combo_stats:
                    visible_levels.append(combo_reverse)

            previous_elements.append(element)

        return visible_levels


    def draw_power_levels_book(self, surface):
        book_rect = self.get_power_levels_book_rect()

        # Primero se dibuja el libro.
        surface.blit(self.power_levels_book, book_rect)

        level_texts = self.get_level_texts()

        # DespuÃ©s se dibujan los poderes sobre sus pÃ¡ginas.
        visible_level_ids = self.get_visible_power_level_ids()

        self.power_level_hitboxes = []

        for stat_id, local_position in zip(
            visible_level_ids,
            self.power_level_positions,
        ):
            image_id = f"lvl_{stat_id}"
            local_x, local_y = local_position

            level_image = self.level_book_images[image_id]

            image_x = (
                book_rect.x
                + local_x * self.pixel_scale
            )

            image_y = (
                book_rect.y
                + local_y * self.pixel_scale
            )

            image_rect = level_image.get_rect(
                topleft=(image_x, image_y)
            )

            self.power_level_hitboxes.append({
                "id": stat_id,
                "rect": image_rect,
            })

            surface.blit(level_image, image_rect)

            plus_book_id = f"{stat_id}_plus"
            has_plus = plus_book_id in self.player.purchased_books

            if has_plus:
                if PLUS_BORDER_STYLE == "pulse":
                    animation_frame = (
                        pygame.time.get_ticks()
                        // PLUS_BORDER_PULSE_STEP_MS
                    )

                    gold_color = PLUS_BORDER_GOLD_COLORS[
                        animation_frame % len(PLUS_BORDER_GOLD_COLORS)
                    ]
                else:
                    gold_color = (190, 110, 15)

                pygame.draw.rect(
                    surface,
                    gold_color,
                    image_rect,
                    self.pixel_scale,
                )

                border_width = image_rect.width
                border_height = image_rect.height
                sweep_length = border_width + border_height
                trail_length = 6 * self.pixel_scale
                sweep_cycle = sweep_length + trail_length * 2
                sweep_duration = (
                    sweep_cycle * PLUS_BORDER_SWEEP_STEP_MS
                )
                full_cycle_duration = (
                    sweep_duration + PLUS_BORDER_SWEEP_COOLDOWN_MS
                )
                cycle_time = (
                    pygame.time.get_ticks() % full_cycle_duration
                )

                if cycle_time < sweep_duration:
                    sweep_position = (
                        (cycle_time // PLUS_BORDER_SWEEP_STEP_MS)
                        * self.pixel_scale
                    )
                else:
                    sweep_position = sweep_cycle

                def get_top_right_point(position):
                    if position < border_width:
                        return image_rect.left + position, image_rect.top

                    return (
                        image_rect.right - self.pixel_scale,
                        image_rect.top + position - border_width,
                    )

                def get_left_bottom_point(position):
                    if position < border_height:
                        return image_rect.left, image_rect.top + position

                    return (
                        image_rect.left + position - border_height,
                        image_rect.bottom - self.pixel_scale,
                    )

                for index, sweep_color in enumerate(PLUS_BORDER_SWEEP_COLORS):
                    trail_position = (
                        sweep_position - index * self.pixel_scale
                    )

                    if not 0 <= trail_position < sweep_length:
                        continue

                    for get_point in (
                        get_top_right_point,
                        get_left_bottom_point,
                    ):
                        sparkle_x, sparkle_y = get_point(trail_position)

                        pygame.draw.rect(
                            surface,
                            sweep_color,
                            (
                                sparkle_x,
                                sparkle_y,
                                self.pixel_scale,
                                self.pixel_scale,
                            ),
                        )

            level_text = self.info_font.render(
                level_texts[stat_id],
                True,
                config.HUD_COLOR,
            )

            level_text_rect = level_text.get_rect(
                center=(
                    image_rect.centerx + 3 * self.pixel_scale,
                    image_rect.centery,
                )
            )

            surface.blit(level_text, level_text_rect)

    def draw(self, surface):
        surface.blit(self.background, (self.offset_x, self.offset_y))

        self.draw_shop_items(surface)

        self.player.visual.draw(surface, self.player.x, self.player.y)
        self.player.draw_player_stats(surface, self.info_font, self.scaled_stat_positions)

        self.draw_prices(surface)
        self.draw_power_levels_book(surface)

        mouse_pos = self.screen_to_virtual(pygame.mouse.get_pos())
        item_type, item = self.get_hovered_shop_item(mouse_pos)

        focus_rect = self.keyboard_targets()[self.focus_index][2] if self.keyboard_mode else None
        for rect, label in ((self.levels_button, self.game.localization.text("ui.shop.levels")), (self.leave_button, self.game.localization.text("ui.shop.leave"))):
            active = rect == focus_rect or (not self.keyboard_mode and rect.collidepoint(mouse_pos))
            color = (244, 239, 216) if active else (173, 184, 183)
            text = self.info_font.render(label, True, color)
            shadow = self.info_font.render(label, True, (15, 21, 25))
            surface.blit(shadow, shadow.get_rect(center=(rect.centerx + 1, rect.centery + 1)))
            surface.blit(text, text.get_rect(center=rect.center))
            if active:
                pygame.draw.line(surface, color, rect.bottomleft, (rect.right, rect.bottom), 1)
        if self.keyboard_mode:
            item_type, item, rect = self.keyboard_targets()[self.focus_index]
            if item is not None:
                # Tiny corner marks keep focus readable without framing the shelf.
                marker = rect
                for x, y, dx, dy in ((marker.left, marker.top, 1, 1),
                                      (marker.right - 1, marker.top, -1, 1),
                                      (marker.left, marker.bottom - 1, 1, -1),
                                      (marker.right - 1, marker.bottom - 1, -1, -1)):
                    pygame.draw.lines(surface, (226, 230, 217), False,
                                      [(x + 2 * dx, y), (x, y), (x, y + 2 * dy)], 1)
            mouse_pos = rect.midright

        hint = self.game.localization.text(self.notice) if self.notice_time > 0 else (self.game.localization.text("ui.shop.hint") if self.keyboard_mode else "")
        if hint:
            text = self.info_font.render(hint, True, (220, 224, 212))
            shadow = self.info_font.render(hint, True, (15, 21, 25))
            surface.blit(shadow, shadow.get_rect(midbottom=(self.VIRTUAL_WIDTH // 2 + 1, 180)))
            surface.blit(text, text.get_rect(midbottom=(self.VIRTUAL_WIDTH // 2, 179)))

        if item is not None and (not self.keyboard_mode or self.focus_age >= .35):
            title, body_lines, hint = self.get_tooltip_content(item_type, item)
            style = self.get_tooltip_style(item_type, item)
            self.draw_tooltip(surface, title, body_lines, hint, mouse_pos, style, item_type, item["id"])


    def scale_layout_point(self, base_point):
        return (
            self.offset_x + base_point[0] * self.pixel_scale + self.pixel_scale // 2,
            self.offset_y + base_point[1] * self.pixel_scale + self.pixel_scale // 2,
        )

    
    def build_layout_rect(self, base_center, base_size):
        width = base_size[0] * self.pixel_scale
        height = base_size[1] * self.pixel_scale

        rect = pygame.Rect(0, 0, width, height)
        rect.x = self.offset_x + base_center[0] * self.pixel_scale - rect.width // 2
        rect.y = self.offset_y + base_center[1] * self.pixel_scale - rect.height // 2
        return rect

    
    def get_hovered_shop_item(self, mouse_pos):
        
        for level_item in self.power_level_hitboxes:
            if level_item["rect"].collidepoint(mouse_pos):
                return "level", level_item

        shop_groups = [
            ("potion", self.potions_in_shop),
            ("power", self.powers_in_shop),
            ("book", self.books_in_shop),
        ]

        for item_type, items in shop_groups:
            for item in items:
                if item["hit_rect"].collidepoint(mouse_pos):
                    return item_type, item

        return None, None
    
    
    def get_power_level_tooltip_data(self, level_id):
        if level_id in self.player.element_stats:
            stats = self.player.element_stats[level_id].copy()
        else:
            stats = self.player.combo_stats[level_id].copy()

        data = {
            "text_key": f"item.level.{level_id}",
            "tooltip_style": level_id,
            **stats,
        }

        data["has_plus_book"] = (
            f"{level_id}_plus" in self.player.purchased_books
        )

        if level_id == "ice":
            data["slow_percent"] = round(
                (1 - stats["slow_multiplier"]) * 100
            )
            data["frost_wave_duration"] = round(
                stats["frost_wave_duration"],
                2,
            )

        elif level_id == "electric":
            data["chain_damage_percent"] = round(
                stats["damage_percentage"] * 100
            )

        elif level_id == "poison":
            data["damage_received_percent"] = round(
                stats["damage_taken_per_stack"] * 100
            )

        elif level_id == "fire_electric":
            data["fragment_damage_percent"] = round(
                stats["damage_multiplier"] * 100
            )

        elif level_id == "ice_poison":
            data["execute_base_percent"] = round(
                stats["execute_base_threshold"] * 100
            )
            data["execute_stack_percent"] = round(
                stats["execute_threshold_per_stack"] * 100
            )

        elif level_id == "electric_poison":
            drain_per_second = stats["drain_per_second"]
            data["overload_total_duration"] = (
                f"{1 / drain_per_second:.2f}"
                if drain_per_second > 0
                else "âˆž"
            )
            data["tick_damage"] = round(
                stats["tick_damage"],
                2,
            )
            data["speed_multiplier"] = round(
                stats["speed_multiplier"],
                2,
            )

        return data


    def get_item_data(self, item_type, item_id):
        if item_type == "potion":
            return config.POTION_DATA[item_id]

        if item_type == "power":
            return config.POWER_DATA[item_id]

        if item_type == "book":
            return config.BOOK_DATA[item_id]
        
        if item_type == "level":
            return self.get_power_level_tooltip_data(item_id)

        return {}
    

    def get_tooltip_style(self, item_type, item):
        item_data = self.get_item_data(item_type, item["id"])
        style_id = item_data.get("tooltip_style", "default")
        return config.TOOLTIP_STYLES.get(style_id, config.TOOLTIP_STYLES["default"])
    

    def measure_text_width(self, text):
        return self.tooltip_font.render(text, True, (255, 255, 255)).get_width()


    def wrap_text(self, text, max_width):
        words = []

        for part in re.split(r"(\[plus\].*?\[/plus\])", text):
            if not part:
                continue

            if part.startswith("[plus]") and part.endswith("[/plus]"):
                words.append(part)
            else:
                words.extend(part.split())

        lines = []
        current = ""

        for word in words:
            candidate = word if not current else current + " " + word

            if self.measure_text_width(candidate) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines
    

    def format_tooltip_line(self, line, format_data, effect_units=None):
        effect_units = effect_units or {}
        for key, value in format_data.items():
            if effect_units.get(key) == "ratio" and isinstance(value, (int, float)):
                line = line.replace(
                    f"{{good_percent:{key}}}",
                    f"[good]{value * 100:.1f}[/good]",
                )
            line = line.replace(f"{{good:{key}}}", f"[good]{value}[/good]")
            line = line.replace(f"{{bad:{key}}}", f"[bad]{value}[/bad]")

        return line.format(**format_data)


    def get_item_detail_lines(self, item_type, item_id, item_data):
        detail_key = f"item.{item_type}.{item_id}.detail"

        if (
            item_type == "level"
            and item_data.get("has_plus_book", False)
        ):
            detail_key = f"item.level.{item_id}.plus_detail"

        detail_lines = list(
            self.game.localization.text(detail_key, [])
        )

        format_data = item_data.copy()

        if "effect" in item_data:
            format_data.update(item_data["effect"])

        if "modifier" in item_data:
            for field, modifier in item_data["modifier"].items():
                format_data[field] = (
                    modifier.get("value")
                    if isinstance(modifier, dict)
                    else modifier
                )

        if item_type == "book":
            if item_id == "ice":
                format_data["slow_percent"] = round(
                    abs(format_data["slow_multiplier"]) * 100
                )

            elif item_id == "electric":
                format_data["chain_damage_percent"] = round(
                    format_data["damage_percentage"] * 100
                )

            elif item_id == "poison":
                format_data["damage_received_percent"] = round(
                    format_data["damage_taken_per_stack"] * 100
                )

            elif item_id == "fire_electric":
                format_data["fragment_damage_percent"] = round(
                    format_data["damage_multiplier"] * 100
                )

            elif item_id == "electric_poison":
                current_drain = self.player.combo_stats["electric_poison"][
                    "drain_per_second"
                ]
                new_drain = current_drain + format_data["drain_per_second"]
                current_duration = 1 / current_drain
                new_duration = 1 / new_drain if new_drain > 0 else float("inf")
                format_data["overload_total_duration"] = (
                    f"{new_duration:.2f}"
                    if new_duration != float("inf")
                    else "âˆž"
                )
                format_data["overload_duration_added"] = (
                    f"{new_duration - current_duration:.2f}"
                    if new_duration != float("inf")
                    else "âˆž"
                )
                format_data["tick_damage"] = round(
                    format_data["tick_damage"],
                    2,
                )

            elif item_id == "ice_electric_plus":
                format_data["electrified_slow_percent"] = round(
                    abs(format_data["electrified_slow_multiplier"]) * 100
                )

        if "chance" in format_data:
            format_data["chance_percent"] = f"{int(format_data['chance'] * 100)}%"

        return [
            self.format_tooltip_line(
                line,
                format_data,
                item_data.get("effect_units"),
            )
            for line in detail_lines
        ]
        

    def get_tooltip_content(self, item_type, item):
        item_id = item["id"]
        item_data = self.get_item_data(item_type, item_id)
        text_key = item_data.get("text_key", f"item.{item_type}.{item_id}")

        keys = pygame.key.get_pressed()
        show_detail = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        title = self.game.localization.text(
            f"{text_key}.name",
            item_id.replace("_", " ").title(),
        )

        title = title.format(**item_data)

        detail_lines = self.get_item_detail_lines(item_type, item_id, item_data)

        if show_detail and detail_lines:
            body_lines = detail_lines
        else:
            short_key = f"{text_key}.short"

            if (
                item_type == "level"
                and item_data.get("has_plus_book", False)
            ):
                short_key = f"{text_key}.plus_short"

            short = self.game.localization.text(short_key, "")
            description = self.game.localization.text(f"{text_key}.description", short)

            description = description.format(**item_data)

            body_lines = description.splitlines()

        hint = ""

        if detail_lines:
            hint_key = "ui.tooltip.release_shift" if show_detail else "ui.tooltip.hold_shift"
            hint = self.game.localization.text(hint_key, "")

        return title, body_lines, hint
    
    def draw_tooltip(self, surface, title, body_lines, hint, mouse_pos, style, item_type, item_id):
        min_width = 110
        max_width = 190

        padding_x = 10
        padding_y = 11

        title_icon_gap = 6
        title_bottom_gap = 4

        separator_top_gap = 3
        separator_bottom_gap = 5

        body_line_gap = 2

        hint_top_gap = 5
        hint_line_gap = 2

        icon_w = self.tooltip_icon_w
        icon_h = self.tooltip_icon_h

        max_text_width = max_width - padding_x * 2

        title_surface = self.tooltip_font.render(
            title,
            True,
            style["title"],
        )

        title_total_width = (
            icon_w
            + title_icon_gap
            + title_surface.get_width()
            + title_icon_gap
            + icon_w
        )

        wrapped_body_lines = []
        for line in body_lines:
            wrapped_body_lines.extend(
                self.wrap_text(line, max_text_width)
            )

        body_surfaces = [
            self.render_tooltip_rich_line(line, style, item_type, item_id)
            for line in wrapped_body_lines
        ]

        plus_line_indexes = [
            index
            for index, line in enumerate(wrapped_body_lines)
            if "[plus]" in line
        ]

        if plus_line_indexes:
            first_plus_line = plus_line_indexes[0]
            last_plus_line = plus_line_indexes[-1]
            plus_block_width = max(
                body_surfaces[index].get_width()
                for index in range(first_plus_line, last_plus_line + 1)
            )
            plus_block_height = sum(
                body_surfaces[index].get_height()
                for index in range(first_plus_line, last_plus_line + 1)
            )
            plus_block_height += (
                last_plus_line - first_plus_line
            ) * body_line_gap

            plus_line_y = 0
            synchronized_body_surfaces = []
            for index, line in enumerate(wrapped_body_lines):
                shine_context = None
                if first_plus_line <= index <= last_plus_line:
                    shine_context = (
                        plus_block_width,
                        plus_block_height,
                        plus_line_y,
                    )

                synchronized_body_surfaces.append(
                    self.render_tooltip_rich_line(
                        line,
                        style,
                        item_type,
                        item_id,
                        shine_context,
                    )
                )

                if first_plus_line <= index <= last_plus_line:
                    plus_line_y += (
                        body_surfaces[index].get_height()
                        + body_line_gap
                    )

            body_surfaces = synchronized_body_surfaces

        hint_surfaces = []
        if hint:
            wrapped_hint_lines = self.wrap_text(hint, max_text_width)
            hint_surfaces = [
                self.tooltip_font.render(line, True, style["accent"])
                for line in wrapped_hint_lines
            ]

        max_line_width = 0

        for text_surface in body_surfaces:
            max_line_width = max(max_line_width, text_surface.get_width())

        for text_surface in hint_surfaces:
            max_line_width = max(max_line_width, text_surface.get_width())

        content_width = max(
            title_total_width,
            max_line_width,
            min_width - padding_x * 2,
        )

        content_width = min(content_width, max_text_width)
        tooltip_width = content_width + padding_x * 2

        tooltip_height = padding_y
        tooltip_height += title_surface.get_height()
        tooltip_height += title_bottom_gap
        tooltip_height += separator_top_gap
        tooltip_height += 1
        tooltip_height += separator_bottom_gap

        if body_surfaces:
            for text_surface in body_surfaces:
                tooltip_height += text_surface.get_height()
                tooltip_height += body_line_gap

            tooltip_height -= body_line_gap

        if hint_surfaces:
            tooltip_height += hint_top_gap
            tooltip_height += 1
            tooltip_height += hint_line_gap

            for text_surface in hint_surfaces:
                tooltip_height += text_surface.get_height()
                tooltip_height += body_line_gap

            tooltip_height -= body_line_gap

        tooltip_height += padding_y

        x = mouse_pos[0] + 8
        y = mouse_pos[1] + 8

        if x + tooltip_width > surface.get_width():
            x = mouse_pos[0] - tooltip_width - 8

        if y + tooltip_height > surface.get_height():
            y = surface.get_height() - tooltip_height - 4

        x = max(4, x)
        y = max(4, y)

        rect = pygame.Rect(x, y, tooltip_width, tooltip_height)

        self.draw_parchment_box(
            surface,
            rect,
            style,
            seed=title,
        )

        current_y = rect.y + padding_y

        title_group_x = rect.centerx - title_total_width // 2
        title_x = title_group_x + icon_w + title_icon_gap
        icon_y = current_y + (title_surface.get_height() - icon_h) // 2

        self.draw_tooltip_icon(
            surface,
            title_group_x,
            icon_y,
            style["icon_left"],
        )

        surface.blit(
            title_surface,
            (title_x, current_y),
        )

        self.draw_tooltip_icon(
            surface,
            title_x + title_surface.get_width() + title_icon_gap,
            icon_y,
            style["icon_right"],
        )

        current_y += title_surface.get_height()
        current_y += title_bottom_gap
        current_y += separator_top_gap

        self.draw_tooltip_separator(
            surface,
            rect.x + padding_x,
            current_y,
            rect.width - padding_x * 2,
            style,
            "big",
        )

        current_y += 1
        current_y += separator_bottom_gap

        for text_surface in body_surfaces:
            surface.blit(
                text_surface,
                (rect.x + padding_x, current_y),
            )

            current_y += text_surface.get_height()
            current_y += body_line_gap

        if hint_surfaces:
            current_y += hint_top_gap

            self.draw_tooltip_separator(
                surface,
                rect.x + padding_x,
                current_y,
                rect.width - padding_x * 2,
                style,
                "small",
            )

            current_y += 1
            current_y += hint_line_gap

            for text_surface in hint_surfaces:
                surface.blit(
                    text_surface,
                    (rect.x + padding_x, current_y),
                )

                current_y += text_surface.get_height()
                current_y += body_line_gap


    def render_plus_tooltip_text(self, text, shine_context=None):
        animation_frame = (
            pygame.time.get_ticks()
            // PLUS_BORDER_PULSE_STEP_MS
        )
        base_color = PLUS_BORDER_GOLD_COLORS[
            animation_frame % len(PLUS_BORDER_GOLD_COLORS)
        ]

        text_surface = self.tooltip_font.render(
            text,
            True,
            base_color,
        )

        shine_width = 4 * self.pixel_scale
        if shine_context:
            block_width, block_height, line_y = shine_context
        else:
            block_width = text_surface.get_width()
            block_height = text_surface.get_height()
            line_y = 0

        sweep_distance = block_width + block_height + shine_width
        sweep_duration = PLUS_TEXT_SHINE_DURATION_MS
        full_cycle_duration = (
            sweep_duration + PLUS_BORDER_SWEEP_COOLDOWN_MS
        )
        cycle_time = pygame.time.get_ticks() % full_cycle_duration

        if cycle_time >= sweep_duration:
            return text_surface

        diagonal_position = int(
            (cycle_time / sweep_duration) * sweep_distance
        ) - shine_width

        for index, shine_color in enumerate(PLUS_BORDER_SWEEP_COLORS):
            shine_surface = self.tooltip_font.render(
                text,
                True,
                shine_color,
            )
            shine_mask = pygame.Surface(
                text_surface.get_size(),
                pygame.SRCALPHA,
            )
            trail_position = (
                diagonal_position
                - line_y
                - index * self.pixel_scale
            )

            pygame.draw.line(
                shine_mask,
                (255, 255, 255, 255),
                (trail_position, 0),
                (
                    trail_position - text_surface.get_height(),
                    text_surface.get_height(),
                ),
                shine_width,
            )

            shine_surface.blit(
                shine_mask,
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
            text_surface.blit(shine_surface, (0, 0))

        return text_surface


    def render_tooltip_rich_line(
        self,
        text,
        style,
        item_type,
        item_id,
        shine_context=None,
    ):
        normal_color = style["text"]
        positive_color = style.get("positive", (35, 90, 45))
        negative_color = style.get("negative", (120, 35, 35))
        plus_color = style.get("plus", (222, 174, 65))

        parts = re.split(
            r"(\[good\].*?\[/good\]|\[bad\].*?\[/bad\]|\[plus\].*?\[/plus\]|[+-]?\d+(?:\.\d+)?%?)",
            text,
        )

        rendered_parts = []

        for part in parts:
            if part == "":
                continue

            color = normal_color
            is_plus_text = False

            if part.startswith("[good]") and part.endswith("[/good]"):
                part = part.replace("[good]", "").replace("[/good]", "")
                color = positive_color

            elif part.startswith("[bad]") and part.endswith("[/bad]"):
                part = part.replace("[bad]", "").replace("[/bad]", "")
                color = negative_color

            elif part.startswith("[plus]") and part.endswith("[/plus]"):
                part = part.replace("[plus]", "").replace("[/plus]", "")
                color = plus_color
                is_plus_text = True

            elif re.fullmatch(r"[+-]?\d+(?:\.\d+)?%?", part):
                if part.startswith("-"):
                    color = negative_color
                else:
                    color = positive_color

            part_surface = (
                self.render_plus_tooltip_text(part, shine_context)
                if is_plus_text
                else self.tooltip_font.render(part, True, color)
            )

            rendered_parts.append((part_surface, part))

        part_gap = self.pixel_scale

        width = sum(
            part_surface.get_width()
            for part_surface, part_text in rendered_parts
        )

        width += max(0, len(rendered_parts) - 1) * part_gap

        height = max(
            (
                part_surface.get_height()
                for part_surface, part_text in rendered_parts
            ),
            default=1,
        )

        line_surface = pygame.Surface(
            (max(1, width), height),
            pygame.SRCALPHA,
        )

        x = 0

        for index, (part_surface, part_text) in enumerate(rendered_parts):
            if index > 0:
                x += part_gap

            line_surface.blit(part_surface, (x, 0))
            x += part_surface.get_width()

        return line_surface

    def draw_parchment_box(self, surface, rect, style, seed="tooltip"):
        rng = random.Random(f"{seed}-{rect.width}-{rect.height}")

        border_points = self.build_torn_paper_points(rect, rng)

        local_points = [
            (x - rect.x, y - rect.y)
            for x, y in border_points
        ]

        border_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

        pygame.draw.lines(
            border_surface,
            style["border"],
            True,
            local_points,
            2,
        )

        interior_mask = self.create_tooltip_interior_mask(border_surface)

        bg_surface = interior_mask.to_surface(
            setcolor=(*style["bg"], 255),
            unsetcolor=(0, 0, 0, 0),
        ).convert_alpha()

        surface.blit(bg_surface, rect.topleft)
        surface.blit(border_surface, rect.topleft)

    def create_tooltip_interior_mask(self, border_surface):
        width = border_surface.get_width()
        height = border_surface.get_height()

        border_mask = pygame.mask.from_surface(border_surface)
        interior_mask = pygame.mask.Mask((width, height), False)

        start = (width // 2, height // 2)

        if border_mask.get_at(start):
            start = self.find_tooltip_fill_start(border_mask, width, height, start)

        queue = [start]
        head = 0
        interior_mask.set_at(start, 1)

        while head < len(queue):
            x, y = queue[head]
            head += 1

            neighbors = [
                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1),
            ]

            for next_x, next_y in neighbors:
                if next_x < 0 or next_x >= width:
                    continue

                if next_y < 0 or next_y >= height:
                    continue

                point = (next_x, next_y)

                if border_mask.get_at(point):
                    continue

                if interior_mask.get_at(point):
                    continue

                interior_mask.set_at(point, 1)
                queue.append(point)

        return interior_mask
    

    def find_tooltip_fill_start(self, border_mask, width, height, start):
        start_x, start_y = start

        for radius in range(1, max(width, height)):
            for y in range(start_y - radius, start_y + radius + 1):
                for x in range(start_x - radius, start_x + radius + 1):
                    if x < 0 or x >= width:
                        continue

                    if y < 0 or y >= height:
                        continue

                    point = (x, y)

                    if not border_mask.get_at(point):
                        return point

        return start


    def inset_tooltip_points(self, points, rect, amount):
        inset = []

        for x, y in points:
            new_x = x
            new_y = y

            if x <= rect.left + amount:
                new_x += amount
            elif x >= rect.right - amount:
                new_x -= amount

            if y <= rect.top + amount:
                new_y += amount
            elif y >= rect.bottom - amount:
                new_y -= amount

            inset.append((new_x, new_y))

        return inset


    def draw_tooltip_icon(self, surface, x, y, icon_id):
        icon = self.tooltip_icons.get(icon_id)

        if icon is not None:
            surface.blit(icon, (x, y))

    def draw_tooltip_separator(self, surface, x, y, width, style, size):
        color = style["accent"]

        ornament_width = 5
        gap = 3
        height = y-3

        left_x = x
        right_x = x + width - ornament_width

        line_start = left_x
        line_end = right_x + gap

        pygame.draw.line(
            surface,
            color,
            (line_start, height),
            (line_end, height),
            1,
        )

        if size == "big":
            self.draw_separator_s(
                surface,
                left_x - 1,
                height - 3,
                color,
                flipped=False,
            )

            self.draw_separator_s(
                surface,
                right_x + gap,
                height - 3,
                color,
                flipped=True,
            )


    def draw_separator_s(self, surface, x, y, color, flipped=False):
        points = [
            (1, 0), (2, 0),
            (0, 1), (0, 2),
            (1, 3), (1, 4),
            (2, 5), (2, 6),
            (0, 7), (1, 7),
        ]

        if flipped:
            points = [
                (2 - px, py)
                for px, py in points
            ]

        for px, py in points:
            surface.set_at((x + px, y + py), color)


    def build_torn_paper_points(self, rect, rng):
        margin = 2
        step = 12
        jitter = 1
        notch_chance = 0.15
        notch_depth = 2

        points = []

        # Arriba
        x = rect.left + margin
        while x < rect.right - margin:
            y = rect.top + margin + rng.randint(-jitter, jitter)
            points.append((x, y))

            if rng.random() < notch_chance:
                points.append((x + step // 2, y + notch_depth))

            x += step + rng.randint(-3, 3)

        points.append((rect.right - margin, rect.top + margin))

        # Derecha
        y = rect.top + margin
        while y < rect.bottom - margin:
            x = rect.right - margin + rng.randint(-jitter, jitter)
            points.append((x, y))

            if rng.random() < notch_chance:
                points.append((x - notch_depth, y + step // 2))

            y += step + rng.randint(-3, 3)

        points.append((rect.right - margin, rect.bottom - margin))

        # Abajo
        x = rect.right - margin
        while x > rect.left + margin:
            y = rect.bottom - margin + rng.randint(-jitter, jitter)
            points.append((x, y))

            if rng.random() < notch_chance:
                points.append((x - step // 2, y - notch_depth))

            x -= step + rng.randint(-3, 3)

        points.append((rect.left + margin, rect.bottom - margin))

        # Izquierda
        y = rect.bottom - margin
        while y > rect.top + margin:
            x = rect.left + margin + rng.randint(-jitter, jitter)
            points.append((x, y))

            if rng.random() < notch_chance:
                points.append((x + notch_depth, y - step // 2))

            y -= step + rng.randint(-3, 3)

        points.append((rect.left + margin, rect.top + margin))

        return points
    
    def load_tooltip_icons(self):
        icons = {}

        for icon_id in ["fire", "ice", "electric", "poison"]:
            image = pygame.image.load(
                asset_path("images", "ui", "tooltip_icons", f"{icon_id}.png")
            ).convert_alpha()

            image = pygame.transform.scale(
                image,
                (self.tooltip_icon_w, self.tooltip_icon_h),
            )

            icons[icon_id] = image

        return icons
