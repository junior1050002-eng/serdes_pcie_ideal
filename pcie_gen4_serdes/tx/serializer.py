import numpy as np

class Serializer:
    def __init__(self, bus_width=32):
        self.bus_width = bus_width

    def serialize(self, parallel_words):
        arr = np.asarray(parallel_words)
        if arr.ndim == 1:
            return arr.astype(int)
        return arr.flatten().astype(int)
