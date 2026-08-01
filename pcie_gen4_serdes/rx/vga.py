import numpy as np

class VariableGainAmplifier:
    def __init__(self, target_vpeak=0.4):
        self.target_vpeak = target_vpeak

    def process(self, input_waveform):
        current_vpeak = np.max(np.abs(input_waveform))
        gain_linear = self.target_vpeak / current_vpeak if current_vpeak > 1e-6 else 1.0
        return input_waveform * gain_linear
