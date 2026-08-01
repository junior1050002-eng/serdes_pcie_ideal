import numpy as np

class HighSpeedSampler:
    def __init__(self, offset_mv=0.0, sensitivity_mv=2.0):
        self.offset_volts = offset_mv * 1e-3
        self.sensitivity_volts = sensitivity_mv * 1e-3

    def sample(self, waveform, sample_indices):
        sampled_v = waveform[sample_indices] - self.offset_volts
        bits = np.where(sampled_v >= 0.0, 1, 0)
        return bits, sampled_v
