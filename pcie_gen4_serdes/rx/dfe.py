import numpy as np

class AdaptiveDFE:
    def __init__(self, num_taps=2, mu=0.005, v_target=0.35, max_tap_limit=0.15):
        self.num_taps = num_taps
        self.mu = mu
        self.v_target = v_target
        self.max_tap_limit = max_tap_limit
        self.taps = np.zeros(num_taps, dtype=float)
        self.symbols_history = np.zeros(num_taps, dtype=float)

    def process_symbol(self, raw_sample):
        feedback = np.dot(self.taps, self.symbols_history)
        dfe_v = raw_sample - feedback
        decision_symbol = 1.0 if dfe_v >= 0.0 else -1.0
        decision_bit = 1 if dfe_v >= 0.0 else 0
        
        error = dfe_v - (decision_symbol * self.v_target)
        self.taps += self.mu * error * self.symbols_history
        self.taps = np.clip(self.taps, -self.max_tap_limit, self.max_tap_limit)
        
        self.symbols_history = np.roll(self.symbols_history, 1)
        self.symbols_history[0] = decision_symbol
        return dfe_v, decision_bit, error
