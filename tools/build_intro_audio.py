"""Render original temporary music and Foley for Grimorium's 20-second intro.

Only the Python standard library is used. There are no sampled recordings,
downloads, third-party compositions, or dependencies. Event timing is shared
with the introductory animatic; keep the pauses when changing this score.
"""

from __future__ import annotations

import argparse
from array import array
import math
from pathlib import Path
import random
import sys
import wave


SAMPLE_RATE = 22050
DURATION = 20.0
TAU = 2.0 * math.pi
ROOT = Path(__file__).resolve().parents[1]


class Mix:
    def __init__(self) -> None:
        self.left = array("f", [0.0]) * round(SAMPLE_RATE * DURATION)
        self.right = array("f", [0.0]) * round(SAMPLE_RATE * DURATION)
        self.random = random.Random(17032026)

    def event(self, start, duration, signal, level=1.0, pan=0.0):
        """Mix a signal with equal-power panning; pan may vary over the event."""
        first = round(start * SAMPLE_RATE)
        length = round(duration * SAMPLE_RATE)
        for index in range(length):
            frame = first + index
            if not 0 <= frame < len(self.left):
                continue
            t = index / SAMPLE_RATE
            position = pan(t / duration) if callable(pan) else pan
            angle = (max(-1.0, min(1.0, position)) + 1.0) * math.pi / 4.0
            value = signal(t) * level
            self.left[frame] += value * math.cos(angle)
            self.right[frame] += value * math.sin(angle)

    def pluck(self, start, midi, duration=0.48, level=0.12, pan=0.0):
        frequency = 440.0 * 2.0 ** ((midi - 69) / 12.0)

        def sample(t):
            attack = min(1.0, t / 0.005)
            tail = min(1.0, (duration - t) / 0.06)
            # Rounded wooden fundamental, with a short inharmonic strike.
            body = math.sin(TAU * frequency * t) * math.exp(-8.0 * t)
            upper = 0.24 * math.sin(TAU * frequency * 2.007 * t) * math.exp(-17.0 * t)
            strike = 0.07 * math.sin(TAU * frequency * 3.96 * t) * math.exp(-30.0 * t)
            return (body + upper + strike) * attack * tail

        self.event(start, duration, sample, level, pan)

    def tap(self, start, level=0.075, pitch=190.0, pan=0.0):
        """A quiet rounded footstep, deliberately smaller than the music."""
        previous = 0.0

        def sample(t):
            nonlocal previous
            previous = 0.70 * previous + 0.30 * self.random.uniform(-1.0, 1.0)
            envelope = min(1.0, t / 0.002) * math.exp(-65.0 * t)
            return (math.sin(TAU * pitch * t) + 0.45 * previous) * envelope

        self.event(start, 0.10, sample, level, pan)

    def rustle(self, start, duration, level=0.05, pan=0.0):
        """Filtered noise; no real-world audio sample is embedded."""
        smooth = 0.0
        low = 0.0

        def sample(t):
            nonlocal smooth, low
            noise = self.random.uniform(-1.0, 1.0)
            smooth = 0.72 * smooth + 0.28 * noise
            low = 0.98 * low + 0.02 * noise
            envelope = math.sin(math.pi * t / duration) ** 1.7
            return (smooth - low) * envelope

        self.event(start, duration, sample, level, pan)

    def swoosh(self, start, duration, level=0.2, pan=0.0):
        filtered = 0.0

        def sample(t):
            nonlocal filtered
            progress = t / duration
            blend = 0.035 + 0.26 * math.sin(math.pi * progress) ** 2
            filtered += blend * (self.random.uniform(-1.0, 1.0) - filtered)
            envelope = math.sin(math.pi * progress) ** 1.6
            phase = TAU * (340.0 * t - 210.0 * t * t / (2.0 * duration))
            return (filtered * 1.4 + 0.16 * math.sin(phase)) * envelope

        self.event(start, duration, sample, level, pan)

    def boing(self, start, duration=0.30, level=0.11, pan=0.0):
        def sample(t):
            phase = TAU * (170.0 * t + 80.0 * duration * (1.0 - math.exp(-t / duration)))
            return math.sin(phase) * min(1.0, t / 0.004) * math.exp(-16.0 * t)

        self.event(start, duration, sample, level, pan)

    def export(self, path):
        # Smooth the outside boundaries before measuring the final peak.
        for index in range(len(self.left)):
            t = index / SAMPLE_RATE
            fade = min(1.0, t / 0.04, (DURATION - t) / 0.25)
            self.left[index] *= fade
            self.right[index] *= fade
        source_peak = max(max(abs(v) for v in self.left), max(abs(v) for v in self.right))
        gain = min(2.0, 0.66 / source_peak) if source_peak else 1.0
        pcm = array("h")
        energy = 0.0
        peak = 0.0
        for left, right in zip(self.left, self.right):
            for value in (left * gain, right * gain):
                peak = max(peak, abs(value))
                energy += value * value
                pcm.append(round(max(-1.0, min(1.0, value)) * 32767.0))
        if sys.byteorder != "little":
            pcm.byteswap()
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as output:
            output.setnchannels(2)
            output.setsampwidth(2)
            output.setframerate(SAMPLE_RATE)
            output.writeframes(pcm.tobytes())
        rms = math.sqrt(energy / len(pcm))
        print(f"Output: {path}")
        print(f"Duration: {len(self.left) / SAMPLE_RATE:.6f} seconds")
        print(f"Format: {SAMPLE_RATE} Hz, stereo, PCM 16-bit")
        print(f"Peak: {peak:.6f} ({20.0 * math.log10(peak):.2f} dBFS)")
        print(f"RMS: {rms:.6f} ({20.0 * math.log10(rms):.2f} dBFS)")
        print("Clipped samples: 0")


def render():
    mix = Mix()
    # An original, restrained, slightly lopsided wooden melody in D Dorian.
    # These explicit pitches were composed for this animatic; they are not a
    # transcription or imitation of either reference game's soundtrack.
    opening = [(0.20, 74), (0.72, 69), (1.00, 77), (1.54, 76),
               (2.08, 79), (2.35, 77), (2.88, 74), (3.43, 76), (3.71, 69)]
    for index, (at, midi) in enumerate(opening):
        mix.pluck(at, midi, level=0.10, pan=-0.18 if index % 2 else 0.18)
    for at, midi in [(0.18, 50), (1.26, 57), (2.34, 50), (3.42, 57)]:
        mix.pluck(at, midi, duration=0.60, level=0.075, pan=-0.08)
    for index in range(9):
        mix.tap(0.35 + index * 0.455, level=0.034, pitch=175 + (index % 2) * 30, pan=0.25)
    mix.rustle(1.35, 0.24, level=0.070, pan=0.25)
    mix.rustle(3.65, 0.25, level=0.062, pan=0.10)

    # Approach builds only a little: this is a comic interruption, not horror.
    mix.swoosh(4.40, 0.95, level=0.10, pan=lambda p: 0.7 - 0.4 * p)
    mix.pluck(4.48, 62, duration=0.55, level=0.05)
    mix.swoosh(5.40, 0.28, level=0.32, pan=lambda p: 0.7 - 1.4 * p)
    mix.tap(5.51, level=0.10, pitch=340.0, pan=-0.15)
    mix.rustle(5.51, 0.16, level=0.11, pan=-0.2)

    # The rest is part of the joke: retain space for the empty-handed stare.
    mix.pluck(6.20, 86, duration=0.16, level=0.057, pan=0.22)
    mix.boing(7.20, duration=0.24, level=0.082, pan=0.16)

    for index in range(5):
        mix.swoosh(8.82 + index * 0.29, 0.17, level=0.073 - index * 0.007,
                   pan=-0.18 - index * 0.13)
    for at, midi in [(8.70, 81), (9.02, 77), (9.65, 79), (10.29, 76), (10.94, 74)]:
        mix.pluck(at, midi, level=0.062, duration=0.44, pan=-0.12)

    # Faster, bouncy variation for the short-legged chase.
    chase = [74, 77, 76, 69, 79, 77, 81, 76, 74, 69, 77, 79, 76, 74, 81, 77, 76, 69]
    for index, midi in enumerate(chase):
        mix.pluck(11.65 + index * 0.315, midi, duration=0.32,
                  level=0.075 if index % 3 else 0.094, pan=0.12 if index % 2 else -0.12)
    for index in range(9):
        mix.pluck(11.66 + index * 0.63, 50 if index % 2 == 0 else 57,
                  duration=0.34, level=0.065, pan=-0.08)
    for index in range(26):
        mix.tap(11.70 + index * 0.215, level=0.044,
                pitch=180 + (index % 2) * 30, pan=0.20 - index * 0.018)

    # A little knock, a moment to collect himself, and a warm resolving button.
    mix.tap(17.75, level=0.115, pitch=125, pan=-0.35)
    mix.tap(17.90, level=0.080, pitch=140, pan=-0.35)
    for at, midi, level in [(18.80, 69, 0.10), (19.03, 73, 0.11), (19.26, 74, 0.14)]:
        mix.pluck(at, midi, duration=min(0.70, DURATION - at), level=level)
    for midi in (50, 57, 66):
        mix.pluck(19.26, midi, duration=0.74, level=0.07, pan=(midi - 57) / 30.0)
    return mix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "assets/video/intro/intro-audio.wav")
    args = parser.parse_args()
    render().export(args.out.resolve())


if __name__ == "__main__":
    main()
