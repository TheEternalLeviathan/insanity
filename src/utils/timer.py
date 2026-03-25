import time
from contextlib import contextmanager

@contextmanager
def timed(name: str, timings: dict):
    start = time.time()
    yield
    timings[name] = round(time.time() - start, 3)
