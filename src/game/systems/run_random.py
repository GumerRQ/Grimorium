"""Stable content streams, isolated from particles and elapsed combat time."""
from contextlib import contextmanager
import random


@contextmanager
def content_random(seed, section):
    state = random.getstate()
    random.seed(f'grimorium-v1:{seed}:{section}', version=2)
    try:
        yield
    finally:
        random.setstate(state)
