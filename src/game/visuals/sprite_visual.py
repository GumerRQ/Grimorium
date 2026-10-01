import pygame

from game.utils.paths import asset_path


class SpriteVisual:
    def __init__(
        self,
        image_folder,
        image_name,
        frame_cols=1,
        frame_rows=1,
        scale_x=32,
        scale_y=32,
        colorkey=None,
        use_alpha=False,
    ):
        image_path = asset_path("images", image_folder, image_name)
        self.source = dict(image_folder=image_folder, image_name=image_name,
                           frame_cols=frame_cols, frame_rows=frame_rows,
                           colorkey=colorkey, use_alpha=use_alpha)

        if use_alpha:
            self.sprite_sheet = pygame.image.load(image_path).convert_alpha()
        else:
            self.sprite_sheet = pygame.image.load(image_path).convert()
            if colorkey is not None:
                self.sprite_sheet.set_colorkey(colorkey)

        self.frame_cols = frame_cols
        self.frame_rows = frame_rows
        self.scale_x = scale_x
        self.scale_y = scale_y

        sheet_width = self.sprite_sheet.get_width()
        sheet_height = self.sprite_sheet.get_height()

        self.frame_width = sheet_width // frame_cols
        self.frame_height = sheet_height // frame_rows

        self.current_surface = None
        self.current_col = 0
        self.current_row = 0

        self.frame_cache = {}
        self.tinted_cache = {}

        self.tint = None

        self.set_frame(0, 0)

    def get_frame(self, col, row):
        frame_rect = pygame.Rect(
            col * self.frame_width,
            row * self.frame_height,
            self.frame_width,
            self.frame_height,
        )
        return self.sprite_sheet.subsurface(frame_rect).copy()

    def reloaded(self):
        sprite = SpriteVisual(**self.source, scale_x=self.scale_x, scale_y=self.scale_y)
        sprite.set_frame(self.current_col, self.current_row)
        sprite.tint = self.tint
        return sprite

    def set_frame(self, col, row):
        self.current_col = col
        self.current_row = row

        cache_key = (col, row, self.scale_x, self.scale_y)

        if cache_key not in self.frame_cache:
            frame = self.get_frame(col, row)
            self.frame_cache[cache_key] = pygame.transform.scale(
                frame,
                (self.scale_x, self.scale_y),
            )

        self.current_surface = self.frame_cache[cache_key]

    def set_size(self, scale_x, scale_y):
        if self.scale_x == scale_x and self.scale_y == scale_y:
            return

        self.scale_x = scale_x
        self.scale_y = scale_y
        self.set_frame(self.current_col, self.current_row)

    def draw(self, surface, x, y):
        rect = self.current_surface.get_rect(center=(int(x), int(y)))
        surface.blit(self.current_surface, rect)
    

    def set_tint(self, color):
        self.tint = color

    def clear_tint(self):
        self.tint = None

    def get_surface(self):
        if self.current_surface is None:
            return None

        if self.tint is None:
            return self.current_surface

        tinted = self.current_surface.copy()

        mask = pygame.mask.from_surface(self.current_surface)
        overlay = mask.to_surface(
            setcolor=self.tint,
            unsetcolor=(0, 0, 0, 0),
        ).convert_alpha()

        tinted.blit(overlay, (0, 0))
        return tinted
