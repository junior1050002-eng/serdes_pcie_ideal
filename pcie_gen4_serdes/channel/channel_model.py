import numpy as np
from scipy.signal import butter, lfilter
from ..config import PCIeGen4Config

class PCIeGen4Channel:
    def __init__(self, loss_db_at_nyquist=28.0):
        self.loss_db_at_nyquist = loss_db_at_nyquist
        self.f_nyq = PCIeGen4Config.DATA_RATE / 2.0

    def transmit(self, time_vec, tx_waveform):
        fs = PCIeGen4Config.FS
        nyq = 0.5 * fs
        cutoff_freq = 2.7e9
        normal_cutoff = cutoff_freq / nyq
        b, a = butter(2, normal_cutoff, btype='low', analog=False)
        rx_input_waveform = lfilter(b, a, tx_waveform)
        return rx_input_waveform
