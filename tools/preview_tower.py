"""Vista del fondo en una sala real, sin combate.

    python tools/preview_tower.py
    python tools/preview_tower.py --headless --output tmp/tower-preview

Flechas: subir/bajar. Inicio/Fin: extremos. R: recargar PNG. Escape: salir.
"""

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "tmp" / "tower-preview")
    args = parser.parse_args()
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    import pygame
    from game import config
    from game.core.game import Game
    from game.rooms.room_data import RANDOM_ROOM_L
    from game.screens.combat_screen import CombatScreen

    class PreviewGame(Game):
        def apply_display_mode(self):
            self.screen = pygame.display.set_mode((1280, 720))

    game = PreviewGame()
    game.run_state.mode = "normal_run"
    game.run_state.current_step = "normal"
    scene = CombatScreen(game, RANDOM_ROOM_L, "normal")
    scene.intro_active = False
    scene.place_player_at_spawn()
    background = game.tower_background
    total = background.total_floors
    floors_per_loop = sum(step in ("normal", "boss") for step in config.RUN_PATTERN)
    floor = 0

    def set_floor(index, immediate=False):
        nonlocal floor
        floor = max(0, min(total - 1, index))
        game.run_state.run_cycles, local_floor = divmod(floor, floors_per_loop)
        game.run_state.room_level = local_floor + 1
        game.run_state.current_step_index = [i for i, s in enumerate(config.RUN_PATTERN) if s in ("normal", "boss")][local_floor]
        background.set_floor(floor, immediate=immediate)
        pygame.display.set_caption(
            f"Grimorium | Altura {floor + 1}/{total} | Flechas: subir/bajar | R: recargar arte | Esc: salir"
        )

    if args.headless:
        args.output.mkdir(parents=True, exist_ok=True)
        selected = (0, (total - 1) // 2, total - 1)
        sheet = pygame.Surface((1280, 3 * 760))
        sheet.fill((23, 28, 33))
        font = pygame.font.Font(None, 30)
        for row, index in enumerate(selected):
            set_floor(index, immediate=True)
            scene.draw(scene.virtual_surface)
            frame = pygame.transform.scale(scene.virtual_surface, (1280, 720))
            filename = args.output / f"floor-{index + 1:02d}.png"
            pygame.image.save(frame, filename)
            sheet.blit(frame, (0, row * 760 + 40))
            label = font.render(f"ALTURA {index + 1:02d}/{total}  -  FLOOR {game.run_state.room_level} / LOOP {game.run_state.run_cycles + 1}", True, (218, 228, 229))
            sheet.blit(label, (24, row * 760 + 10))
            print(filename)
        pygame.image.save(sheet, args.output / "progression.png")
        print(args.output / "progression.png")
        pygame.quit()
        return

    set_floor(0, immediate=True)
    running = True
    while running:
        dt = min(game.clock.tick(config.FPS) / 1000, .1)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_RIGHT, pygame.K_UP, pygame.K_SPACE):
                    set_floor(floor + 1)
                elif event.key in (pygame.K_LEFT, pygame.K_DOWN):
                    set_floor(floor - 1)
                elif event.key == pygame.K_HOME:
                    set_floor(0)
                elif event.key == pygame.K_END:
                    set_floor(total - 1)
                elif event.key == pygame.K_r:
                    game.tower_background = None
                    scene.setup_background()
                    background = game.tower_background
                    set_floor(floor, immediate=True)
        background.update(dt)
        scene.draw(scene.virtual_surface)
        pygame.transform.scale(scene.virtual_surface, (1280, 720), game.screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
