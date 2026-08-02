import numpy as np

class HighSpeedSampler:
    def __init__(self, offset_mv=8.0, sensitivity_mv=3.0, enable_non_idealities=False):
        self.offset_volts = (offset_mv * 1e-3) if enable_non_idealities else 0.0
        self.sensitivity_volts = (sensitivity_mv * 1e-3) if enable_non_idealities else 0.0
        self.enable_non_idealities = enable_non_idealities

    def sample(self, waveform, sample_indices):
        sampled_v = waveform[sample_indices] - self.offset_volts
        
        if self.enable_non_idealities:
            bits = np.where(sampled_v >= self.sensitivity_volts, 1,
                   np.where(sampled_v <= -self.sensitivity_volts, 0, 
                   np.random.choice([0, 1], size=len(sampled_v))))
        else:
            bits = np.where(sampled_v >= 0.0, 1, 0)
            
        return bits, sampled_v
