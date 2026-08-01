import numpy as np

class PRBSGenerator:
    POLYNOMIALS = {
        7:  (7, [7, 6]),
        15: (15, [15, 14]),
        23: (23, [23, 18]),
        31: (31, [31, 28])
    }

    def __init__(self, order=7, seed=None):
        if order not in self.POLYNOMIALS:
            raise ValueError(f"Unsupported PRBS order {order}.")
        self.order = order
        self.nbits, self.taps = self.POLYNOMIALS[order]
        self.state = (1 << self.nbits) - 1 if seed is None else seed

    def generate(self, num_bits=1000):
        bits = np.zeros(num_bits, dtype=int)
        mask = (1 << self.nbits) - 1
        state = self.state
        for i in range(num_bits):
            feedback = 0
            for tap in self.taps:
                feedback ^= (state >> (self.nbits - tap)) & 1
            bits[i] = state & 1
            state = ((state >> 1) | (feedback << (self.nbits - 1))) & mask
        self.state = state
        return bits
