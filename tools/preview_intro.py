"""Preview or export the exact in-game intro. Requires pygame.

Interactive: py tools/preview_intro.py
Export: py tools/preview_intro.py --export output/intro/intro-v1.mp4
Optional export dependency: imageio-ffmpeg, or ffmpeg on PATH.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def get_ffmpeg():
    binary = shutil.which("ffmpeg")
    if binary:
        return binary
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise SystemExit("Para exportar: py -m pip install imageio-ffmpeg") from exc


def export_video(sequence, path, fps, output_size):
    import pygame
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = sequence.size
    if width % 2 or height % 2:
        raise SystemExit("El vídeo H.264 requiere dimensiones pares.")
    command = [get_ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps),
               "-i", "pipe:0"]
    audio = sequence.root / "intro-audio.wav"
    if audio.is_file():
        command += ["-i", str(audio), "-c:a", "aac", "-b:a", "128k"]
    command += ["-vf", f"scale={output_size[0]}:{output_size[1]}:flags=neighbor",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
                "-t", str(sequence.duration), "-movflags", "+faststart", str(path)]
    frame = pygame.Surface(sequence.size)
    log_path = path.with_suffix(".export.log")
    with log_path.open("wb") as errors:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=errors,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            count = math.ceil(sequence.duration * fps)
            for i in range(count):
                sequence.draw(frame, i / fps)
                proc.stdin.write(pygame.image.tobytes(frame, "RGB"))
                if i % (fps * 5) == 0:
                    print(f"Exportando {i / fps:.0f}/{sequence.duration:.0f} s", flush=True)
            proc.stdin.close()
            code = proc.wait(timeout=90)
            if code:
                raise RuntimeError(f"FFmpeg falló ({code}); consulta {log_path}")
        except BaseException:
            proc.kill()
            proc.wait()
            raise
    print(path)


def contact_sheet(sequence, path):
    import pygame
    # Deterministic renderer samples for QA; no source art is changed.
    times = [.8, 3.6, 5.25, 5.53, 6.4, 7.2, 9.1, 10.7, 12.3, 13.8, 16.6, 19.5]
    thumb = sequence.size
    sheet = pygame.Surface((thumb[0] * 3, (thumb[1] + 28) * 4))
    sheet.fill((22, 25, 31))
    font = pygame.font.Font(None, 20)
    frame = pygame.Surface(sequence.size)
    for i, t in enumerate(times):
        sequence.draw(frame, t)
        x, y = (i % 3) * thumb[0], (i // 3) * (thumb[1] + 28)
        sheet.blit(frame, (x, y))
        beat, _ = sequence.beat_at(t)
        label = f"{t:.2f}s · {beat['label']}"
        sheet.blit(font.render(label, True, (236, 230, 217)), (x + 9, y + thumb[1] + 5))
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(sheet, str(path))
    print(path.resolve())


def interactive(sequence, output_size):
    import pygame
    screen = pygame.display.set_mode(output_size)
    frame = pygame.Surface(sequence.size)
    pygame.display.set_caption("Grimorium — montaje de la intro")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 22)
    elapsed, paused, muted, active = 0.0, False, False, True
    sound = None
    if pygame.mixer.get_init():
        try:
            sound = pygame.mixer.Sound(str(sequence.root / "intro-audio.wav"))
        except (pygame.error, OSError):
            pass
    channel = sound.play() if sound else None
    while active:
        dt = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                active = False
            elif event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                if event.key == pygame.K_ESCAPE:
                    active = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    if channel:
                        channel.pause() if paused else channel.unpause()
                elif event.key == pygame.K_r:
                    elapsed, paused = 0.0, False
                    if channel:
                        channel.stop()
                    channel = sound.play() if sound else None
                    if channel:
                        channel.set_volume(0 if muted else 1)
                elif event.key == pygame.K_m:
                    muted = not muted
                    if channel:
                        channel.set_volume(0 if muted else 1)
        if not paused:
            elapsed = min(sequence.duration, elapsed + dt)
        sequence.draw(frame, elapsed)
        pygame.transform.scale(frame, output_size, screen)
        hint = font.render("Espacio: pausa   R: repetir   M: sonido   Esc: salir", True, (255, 255, 255))
        screen.blit(hint, (16, screen.get_height() - 28))
        pygame.display.flip()
    if channel:
        channel.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument("--width", type=int, default=1280,
                        help="Anchura de salida, múltiplo de 320; dibujo interno siempre a 320 × 180")
    parser.add_argument("--fps", type=int, default=24)
    args = parser.parse_args()
    if args.width < 320 or args.width % 320 or args.fps < 1:
        parser.error("La anchura debe ser un múltiplo positivo de 320 y los FPS positivos")
    if args.export or args.contact_sheet:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    from game.visuals.intro_sequence import IntroSequence
    pygame.init()
    pygame.display.set_mode((1, 1))
    try:
        sequence = IntroSequence()
        output_size = (args.width, args.width * 9 // 16)
        if args.contact_sheet:
            contact_sheet(sequence, args.contact_sheet)
        if args.export:
            export_video(sequence, args.export, args.fps, output_size)
        if not args.export and not args.contact_sheet:
            interactive(sequence, output_size)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
