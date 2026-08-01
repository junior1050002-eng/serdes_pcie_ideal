import numpy as np
from .prbs_generator import PRBSGenerator
from .serializer import Serializer
from .ffe_equalizer import TXFFEEqualizer
from .tx_driver import TXDriver

class TXTop:
    def __init__(self, prbs_order=7, preset_name="P7", enable_non_idealities=False):
        self.prbs = PRBSGenerator(order=prbs_order)
        self.serializer = Serializer(bus_width=32)
        self.ffe = TXFFEEqualizer(preset_name=preset_name, enable_non_idealities=enable_non_idealities)
        self.driver = TXDriver(enable_non_idealities=enable_non_idealities)

    def run(self, num_bits=2000, preset_name=None):
        if preset_name is not None:
            self.ffe.preset_name = preset_name
            self.ffe.taps = np.array(self.ffe.taps)
        
        bits = self.prbs.generate(num_bits)
        serial_bits = self.serializer.serialize(bits)
        ffe_symbols = self.ffe.process(serial_bits)
        time_vec, tx_waveform = self.driver.generate_waveform(ffe_symbols)
        
        return time_vec, tx_waveform, serial_bits, ffe_symbols
