import numpy as np

class DigitalCDR:
    def __init__(self, kp=0.05, ki=0.005, pi_resolution_bits=6):
        self.kp = kp
        self.ki = ki
        self.pi_steps = 2 ** pi_resolution_bits
        self.phase_acc = 0.0
        self.freq_acc = 0.0

    def update(self, early_late):
        self.freq_acc += self.ki * early_late
        phase_step = self.kp * early_late + self.freq_acc
        self.phase_acc += phase_step
        return self.phase_acc
