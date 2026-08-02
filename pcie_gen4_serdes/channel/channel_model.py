import numpy as np
from scipy.signal import butter, lfilter
from ..config import PCIeGen4Config

class PCIeGen4Channel:
    def __init__(self, loss_db_at_nyquist=28.0, snr_db=25.0, enable_non_idealities=False):
        self.loss_db_at_nyquist = loss_db_at_nyquist
        self.snr_db = snr_db
        self.enable_non_idealities = enable_non_idealities
        self.f_nyq = PCIeGen4Config.DATA_RATE / 2.0

    def transmit(self, time_vec, tx_waveform):
        fs = PCIeGen4Config.FS
        nyq = 0.5 * fs
        cutoff_freq = 2.7e9
        normal_cutoff = cutoff_freq / nyq
        b, a = butter(2, normal_cutoff, btype='low', analog=False)
        rx_input_waveform = lfilter(b, a, tx_waveform)
        
        if self.enable_non_idealities:
            signal_power = np.mean(rx_input_waveform ** 2)
            snr_linear = 10 ** (self.snr_db / 10.0)
            noise_power = signal_power / snr_linear
            noise = np.random.normal(0, np.sqrt(noise_power), size=len(rx_input_waveform))
            rx_input_waveform += noise
            
        return rx_input_waveform
