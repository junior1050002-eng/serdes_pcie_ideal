import numpy as np

class PRBSGenerator:
    """
    PRBS Pattern Generator supporting PRBS7, PRBS15, PRBS23, and PRBS31.
    IEEE / OIF-CEI compliant Polynomials.
    """
    POLYNOMIALS = {
        7:  (7, [7, 6]),       # x^7 + x^6 + 1
        15: (15, [15, 14]),   # x^15 + x^14 + 1
        23: (23, [23, 18]),   # x^23 + x^18 + 1
        31: (31, [31, 28])    # x^31 + x^28 + 1
    }

    def __init__(self, order=7, seed=None):
        if order not in self.POLYNOMIALS:
            raise ValueError(f"Unsupported PRBS order {order}. Supported: {list(self.POLYNOMIALS.keys())}")
        self.order = order
        self.nbits, self.taps = self.POLYNOMIALS[order]
        
        if seed is None:
            self.state = (1 << self.nbits) - 1  # All ones
        else:
            self.state = seed & ((1 << self.nbits) - 1)
            if self.state == 0:
                self.state = 1

    def generate(self, num_bits=1000):
        """Generates a sequence of num_bits (0 or 1)."""
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