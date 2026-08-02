import numpy as np
from scipy.signal import bilinear, lfilter
from ..config import PCIeGen4Config

class ContinuousTimeLinearEqualizer:
    def __init__(self, dc_gain_db=-3.0, peaking_boost_db=12.0, f_nyquist_hz=8e9, enable_non_idealities=False):
        self.dc_gain_db = dc_gain_db
        self.peaking_boost_db = peaking_boost_db
        self.f_nyquist_hz = f_nyquist_hz
        self.enable_non_idealities = enable_non_idealities

    def filter_signal(self, time_vec, input_waveform):
        a_dc = 10 ** (self.dc_gain_db / 20.0)
        boost = 10 ** (self.peaking_boost_db / 20.0)
        w_nyq = 2 * np.pi * self.f_nyquist_hz
        w_z = w_nyq / boost
        w_p1 = w_nyq
        w_p2 = w_nyq * 3.0
        
        num_s = [a_dc / w_z, a_dc]
        den_s = [1.0 / (w_p1 * w_p2), (1.0 / w_p1 + 1.0 / w_p2), 1.0]
        
        fs = PCIeGen4Config.FS
        b_d, a_d = bilinear(num_s, den_s, fs=fs)
        ctle_out = lfilter(b_d, a_d, input_waveform)
        
        if self.enable_non_idealities:
            v_sat = 0.35
            ctle_out = v_sat * np.tanh(ctle_out / v_sat)
            
        return ctle_out
