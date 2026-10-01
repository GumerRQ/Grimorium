"""All tower floors share a 13-column, 11-row frame.

Eight interior rows sit between aligned double doors. Spaces are solid
inaccessible structure; enclosed spaces are dark shafts. V is a floor pit.
"""
import random
from game.rooms.custom_rooms import active_rooms


def tower_room(rows):
    if len(rows) != 8 or any(len(row) > 13 for row in rows):
        raise ValueError("Tower rooms require eight interior rows of at most 13 cells")
    return [" " * 13, "         Dd  ",
            *(row.ljust(13) for row in rows), "         Aa  "]


BOSS_ROOM_1 = tower_room([
    ".............", "......B......", ".............", ".............",
    ".............", ".............", ".............", "..........P..",
])
BOSS_ROOM_2 = tower_room([
    ".............", ".OOO..B..OOO.", ".............", ".OOO.....OOO.",
    ".............", ".............", ".............", "..........P..",
])
RANDOM_ROOM_1 = tower_room([
    ".............", "..E...E...E..", ".............", ".....OOO.....",
    ".....OOO.....", ".............", ".............", "..........P..",
])
RANDOM_ROOM_2 = tower_room([
    "OO..........O", "..E...E...E..", "....E...E....", "VVVV.....VVVV",
    ".............", ".............", "OO.........OO", "..........P..",
])
RANDOM_ROOM_L = tower_room([
    ".............", ".E..E........", ".....E...    ", "E......E.    ",
    ".........    ", ".............", ".............", "..........P..",
])
RANDOM_ROOM_O = tower_room([
    ".....E.......", ".E....E......", "...       ...", "...       .E.",
    "...       ...", "...       ...", ".............", "..E.......P..",
])
RANDOM_ROOM_SMALL = tower_room([
    "         ..  ", "  .........  ", "  .E....E..  ", "  .........  ",
    "  ....O....  ", "  .E.......  ", "  .........  ", "         .P  ",
])
# Optional layouts use the same frame and connected entrance/exit corridors.
RANDOM_ROOM_S = tower_room([
    ".............", ".           .", ".           .", ".............",
    "            .", "            .", ".............", "         .P..",
])
RANDOM_ROOM_BOX = tower_room([
    "..E.E..E..E..", ".............", "EEEEEEEEEEEEE", "VVVV.....VVVV",
    ".....E.......", ".E...........", ".............", "..........P..",
])
RANDOM_ROOM_ZAP = tower_room([
    "EVVV.......VE", "VVVV....V..VV", "VVVV....VVVE", "VVEV....VEVV",
    "VVVV....VVVE", "VVVV....VEVV", "EVVV.......VE", "VV.......P.VV",
])
RANDOM_ROOM_CROSS = tower_room([
    "     ......  ", "     ....    ", ".............", "....E........",
    ".............", ".............", "    .......  ", "    .....P.  ",
])
NORMAL_ROOMS = [RANDOM_ROOM_1, RANDOM_ROOM_2, RANDOM_ROOM_L, RANDOM_ROOM_O,
                RANDOM_ROOM_SMALL]
BOSS_ROOMS = [BOSS_ROOM_1, BOSS_ROOM_2]


def get_random_normal_room():
    return random.choice(NORMAL_ROOMS + active_rooms("normal"))


def get_random_boss_room():
    return random.choice(BOSS_ROOMS + active_rooms("boss"))
