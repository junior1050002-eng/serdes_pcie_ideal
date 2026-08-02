import numpy as np
from .ctle import ContinuousTimeLinearEqualizer
from .vga import VariableGainAmplifier
from .sampler import HighSpeedSampler
from .dfe import AdaptiveDFE
from .cdr import DigitalCDR
from ..config import PCIeGen4Config

class RXTop:
    def __init__(self, ctle_boost_db=12.0, dfe_taps=2, enable_non_idealities=False):
        self.ctle = ContinuousTimeLinearEqualizer(peaking_boost_db=ctle_boost_db, enable_non_idealities=enable_non_idealities)
        self.vga = VariableGainAmplifier(target_vpeak=0.4)
        self.sampler = HighSpeedSampler(offset_mv=8.0, sensitivity_mv=3.0, enable_non_idealities=enable_non_idealities)
        self.dfe = AdaptiveDFE(num_taps=dfe_taps, mu=0.005)
        self.cdr = DigitalCDR()
        self.enable_non_idealities = enable_non_idealities

    def run_equalization(self, time_vec, channel_output_waveform, original_bits):
        ctle_out = self.ctle.filter_signal(time_vec, channel_output_waveform)
        vga_out = self.vga.process(ctle_out)
        
        samples_per_ui = PCIeGen4Config.SAMPLES_PER_UI
        num_bits = len(original_bits)
        
        ideal_nrz = np.repeat(np.where(original_bits > 0, 0.4, -0.4), samples_per_ui)
        corr = np.correlate(vga_out, ideal_nrz, mode='full')
        delay_samples = np.argmax(corr) - (len(ideal_nrz) - 1)
        if delay_samples < 0:
            delay_samples = 0
            
        dfe_sampled_v, rx_recovered_bits = [], []
        
        for i in range(num_bits):
            sample_jitter = int(np.random.normal(0, 1.5)) if self.enable_non_idealities else 0
            sample_idx = delay_samples + i * samples_per_ui + (samples_per_ui // 2) + sample_jitter
            
            if sample_idx >= len(vga_out) or sample_idx < 0:
                break
                
            raw_v = vga_out[sample_idx]
            dfe_v, dec_bit, _ = self.dfe.process_symbol(raw_v)
            
            dfe_sampled_v.append(dfe_v)
            rx_recovered_bits.append(dec_bit)
            
        dfe_sampled_v = np.array(dfe_sampled_v)
        rx_recovered_bits = np.array(rx_recovered_bits)
        
        valid_len = len(rx_recovered_bits)
        skip = 100
        ber = np.sum(rx_recovered_bits[skip:] != original_bits[skip:valid_len]) / float(valid_len - skip) if valid_len > skip else 1.0
        
        return ctle_out, vga_out, dfe_sampled_v, rx_recovered_bits, ber
