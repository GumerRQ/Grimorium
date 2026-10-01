from game.systems.content_loader import load_shop_content

SCREEN_WIDTH = 1280     # 3840, 2560, 1920, 1280
SCREEN_HEIGHT = 720    # 2160, 1440, 1080, 720 
FPS = 60
WINDOW_TITLE = "Grimorium"

ROOM_CELL_SIZE = 32

BACKGROUND_COLOR = (30, 30, 40)

# Paisaje exterior de la torre. El arte editable vive en images/backgrounds/tower.
TOWER_ASCENT_SECONDS = 1
TOWER_ZOOM_PER_FLOOR = 0.07
TOWER_MIN_GROUND_SCALE = 0.32
TOWER_CLOUD_SPEED = 1.5
TOWER_LANDSCAPE_SEED = 74129
PLAYER_COLOR = (80, 220, 120)
PLAYER_COLOR_INVENCIBLE = (160, 255, 180)
ENEMY_COLOR = (220, 90, 90)
ENEMY_BULLET_COLOR = (220, 30, 30)
HUD_COLOR = (255, 255, 255)


PLAYER_RADIUS = 12

PLAYER_SPEED = 100
PLAYER_MAX_HEALTH = 6
PLAYER_FIRE_COOLDOWN = 0.45
PLAYER_DAMAGE = 1
PLAYER_BODY_DAMAGE = 0
PLAYER_LUCK = 0
PLAYER_SHOOT_DISTANCE = 120
PLAYER_INVULNERABILITY_TIME = 1
PLAYER_COINS = 5

PLUS_BOOK_MIN_PURCHASED_BOOKS = 0
PLUS_BOOK_APPEAR_CHANCE = 1


FORWARD_BONUS = 40
SIDE_DRIFT = 47

BULLET_RADIUS = 3
BULLET_SPEED = 180
BULLET_DAMAGE = 1


ENEMY_RADIUS = 10
ENEMY_SPEED = 45
ENEMY_MAX_HEALTH = 6
ENEMY_DAMAGE = 1
ENEMY_BODY_DAMAGE = 1

SHOOTER_ENEMY_BULLET_SPEED = 115
SHOOTER_ENEMY_FIRE_COOLDOWN = 3
SHOOTER_ENEMY_SHOOT_DISTANCE = 120

BOSS_MAX_HEALTH = 100
BOSS_RADIUS = 24
BOSS_REGEN = 0.5
BOSS_DAMAGE = 1
BOSS_BODY_DAMAGE = 2


FONT_SIZE = 20
FONT_FAMILY = "pixel"
PIXEL_FONT_IMAGE = "3x5light.png"


RUN_PATTERN = [
    "normal",
    "shop",
    "normal",
    "shop",
    "normal",
    "shop",
    "normal",
    "shop",
    "normal",
    "shop",
    "boss",
    "shop",
]

POTION_DATA, POWER_DATA, BOOK_DATA = load_shop_content()
POTION_PRICE = next(iter(POTION_DATA.values()))["price"]
POWER_PRICE = next(iter(POWER_DATA.values()))["price"]
BOOK_PRICE = next(iter(BOOK_DATA.values()))["price"]


TOOLTIP_STYLES = {
    "default": {
        "bg": (224, 190, 126),
        "border": (72, 43, 25),
        "title": (78, 43, 34),
        "text": (75, 55, 40),
        "accent": (140, 82, 42),
        "icon_left": "diamond",
        "icon_right": "diamond",
        "positive": (38, 92, 45),
        "negative": (125, 38, 34),
    },

    "fire": {
        "bg": (232, 181, 113),
        "border": (92, 39, 24),
        "title": (135, 45, 24),
        "text": (70, 45, 35),
        "accent": (180, 70, 32),
        "plus": (125, 108, 5),
        "icon_left": "fire",
        "icon_right": "fire",
    },

    "ice": {
        "bg": (214, 198, 145),
        "border": (57, 67, 72),
        "title": (56, 91, 106),
        "text": (61, 58, 49),
        "accent": (83, 130, 148),
        "icon_left": "ice",
        "icon_right": "ice",
    },

    "electric": {
        "bg": (229, 197, 121),
        "border": (82, 61, 25),
        "title": (124, 86, 22),
        "text": (68, 56, 37),
        "accent": (180, 130, 30),
        "icon_left": "electric",
        "icon_right": "electric",
    },

    "poison": {
        "bg": (220, 188, 139),
        "border": (67, 48, 76),
        "title": (96, 58, 122),
        "text": (64, 52, 58),
        "accent": (135, 78, 160),
        "icon_left": "poison",
        "icon_right": "poison",
    },

    "fire_ice": {
        "bg": (232, 181, 113),
        "border": (92, 39, 24),
        "title": (135, 45, 24),
        "text": (61, 58, 49),
        "accent": (83, 130, 148),
        "icon_left": "fire",
        "icon_right": "ice",
    },

    "fire_electric": {
        "bg": (232, 181, 113),
        "border": (92, 39, 24),
        "title": (135, 45, 24),
        "text": (68, 56, 37),
        "accent": (180, 130, 30),
        "icon_left": "fire",
        "icon_right": "electric",
    },

    "ice_electric": {
        "bg": (214, 198, 145),
        "border": (57, 67, 72),
        "title": (56, 91, 106),
        "text": (68, 56, 37),
        "accent": (180, 130, 30),
        "icon_left": "ice",
        "icon_right": "electric",
    },

    "fire_poison": {
        "bg": (232, 181, 113),
        "border": (92, 39, 24),
        "title": (135, 45, 24),
        "text": (64, 52, 58),
        "accent": (135, 78, 160),
        "icon_left": "poison",
        "icon_right": "fire",
    },

    "ice_poison": {
        "bg": (214, 198, 145),
        "border": (57, 67, 72),
        "title": (56, 91, 106),
        "text": (64, 52, 58),
        "accent": (135, 78, 160),
        "icon_left": "ice",
        "icon_right": "poison",
    },

    "electric_poison": {
        "bg": (229, 197, 121),
        "border": (82, 61, 25),
        "title": (124, 86, 22),
        "text": (64, 52, 58),
        "accent": (135, 78, 160),
        "icon_left": "electric",
        "icon_right": "poison",
    },
}
