import numpy as np
from scipy.signal import butter, lfilter
from ..config import PCIeGen4Config

class TXDriver:
    def __init__(self, bandwidth_hz=12e9, rj_ps=0.8, sj_amp_ps=1.5, sj_freq_hz=100e6, dcd_percent=2.0, v_swing=PCIeGen4Config.V_SWING_P2P, enable_non_idealities=False):
        self.bandwidth_hz = bandwidth_hz
        self.rj_ps = rj_ps
        self.sj_amp_ps = sj_amp_ps
        self.sj_freq_hz = sj_freq_hz
        self.dcd_percent = dcd_percent
        self.v_swing = v_swing
        self.enable_non_idealities = enable_non_idealities

    def generate_waveform(self, ffe_symbols):
        num_bits = len(ffe_symbols)
        samples_per_ui = PCIeGen4Config.SAMPLES_PER_UI
        dt, ui = PCIeGen4Config.DT, PCIeGen4Config.UI
        
        total_samples = num_bits * samples_per_ui
        time_vec = np.arange(total_samples) * dt
        bit_edges = np.arange(num_bits + 1) * ui
        
        if self.enable_non_idealities:
            sj_phase = 2 * np.pi * self.sj_freq_hz * bit_edges
            sj_jitter = (self.sj_amp_ps * 1e-12) * np.sin(sj_phase)
            rj_jitter = np.random.normal(0, self.rj_ps * 1e-12, size=num_bits + 1)
            dcd_jitter = np.where(np.arange(num_bits + 1) % 2 == 1, (self.dcd_percent / 100.0) * ui, 0.0)
            bit_edges = bit_edges + sj_jitter + rj_jitter + dcd_jitter

        raw_waveform = np.zeros(total_samples)
        scaled_symbols = ffe_symbols * (self.v_swing / 2.0)
        
        for i in range(num_bits):
            t_start, t_end = bit_edges[i], bit_edges[i+1]
            mask = (time_vec >= t_start) & (time_vec < t_end)
            raw_waveform[mask] = scaled_symbols[i]
            
        bw = self.bandwidth_hz if self.enable_non_idealities else 16e9
        fs = PCIeGen4Config.FS
        nyq = 0.5 * fs
        normal_cutoff = bw / nyq
        b, a = butter(1, normal_cutoff, btype='low', analog=False)
        tx_waveform = lfilter(b, a, raw_waveform)

        if self.enable_non_idealities:
            v_sat = 0.38
            tx_waveform = v_sat * np.tanh(tx_waveform / v_sat)

        return time_vec, tx_waveform
