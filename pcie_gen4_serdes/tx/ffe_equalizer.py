import numpy as np
from ..config import PCIeGen4Config

class TXFFEEqualizer:
    def __init__(self, preset_name="P7", dac_bits=None, enable_non_idealities=False):
        self.preset_name = preset_name
        self.dac_bits = dac_bits
        self.enable_non_idealities = enable_non_idealities
        self.taps = np.array(PCIeGen4Config.get_preset_taps(preset_name), dtype=float)

    def process(self, bits):
        nrz_symbols = np.where(bits > 0, 1.0, -1.0)
        c_pre, c_main, c_post = self.taps
        padded = np.pad(nrz_symbols, (1, 1), mode='edge')
        
        x_pre = padded[2:]
        x_main = padded[1:-1]
        x_post = padded[:-2]
        
        ffe_symbols = c_pre * x_pre + c_main * x_main + c_post * x_post
        
        if self.enable_non_idealities and self.dac_bits is not None:
            levels = 2 ** self.dac_bits
            v_max, v_min = 1.0, -1.0
            step = (v_max - v_min) / (levels - 1)
            ffe_symbols = np.round((ffe_symbols - v_min) / step) * step + v_min
            
        return ffe_symbols
