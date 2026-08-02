import os

# PCIe Gen 4 SerDes 完整非理想 (Non-Ideal) 專案建立腳本 (修正版)
files = {
    "pcie_gen4_serdes/__init__.py": "# PCIe Gen 4 SerDes Package\n",
    
    "pcie_gen4_serdes/config.py": '''"""
PCIe Gen 4 (16 Gbps NRZ) Physical Layer Simulation Parameters
"""

class PCIeGen4Config:
    # Basic Timing & Rate Specs
    DATA_RATE = 16e9                   # 16 Gbps
    UI = 1.0 / DATA_RATE              # Unit Interval: 62.5 ps
    SAMPLES_PER_UI = 64                # OSR for transient analog waveform
    FS = DATA_RATE * SAMPLES_PER_UI   # Sampling Frequency: 1.024 THz
    DT = 1.0 / FS                     # Time step: ~0.9765 ps

    # TX Voltage Specs
    V_SWING_P2P = 0.8                  # 800 mVppd
    V_HIGH = V_SWING_P2P / 2.0         # +400 mV
    V_LOW = -V_SWING_P2P / 2.0         # -400 mV

    # PCI-SIG FFE Presets
    PRESETS = {
        "P0":  {"pre": 0.00,  "post": -0.250, "description": "-6.0 dB De-emphasis, 0.0 dB Pre-shoot"},
        "P1":  {"pre": 0.00,  "post": -0.166, "description": "-3.5 dB De-emphasis, 0.0 dB Pre-shoot"},
        "P2":  {"pre": 0.00,  "post": -0.200, "description": "-4.4 dB De-emphasis, 0.0 dB Pre-shoot"},
        "P3":  {"pre": 0.00,  "post": -0.125, "description": "-2.5 dB De-emphasis, 0.0 dB Pre-shoot"},
        "P4":  {"pre": 0.00,  "post": 0.000,  "description": "0.0 dB Flat (No Equalization)"},
        "P5":  {"pre": 0.10,  "post": 0.000,  "description": "+1.9 dB Pre-shoot, 0.0 dB De-emphasis"},
        "P6":  {"pre": 0.125, "post": 0.000,  "description": "+2.5 dB Pre-shoot, 0.0 dB De-emphasis"},
        "P7":  {"pre": 0.125, "post": -0.200, "description": "-6.0 dB De-emphasis, +3.5 dB Pre-shoot"},
        "P8":  {"pre": 0.125, "post": -0.125, "description": "-3.5 dB De-emphasis, +3.5 dB Pre-shoot"},
        "P9":  {"pre": 0.166, "post": 0.000,  "description": "+3.5 dB Pre-shoot, 0.0 dB De-emphasis"},
        "P10": {"pre": 0.00,  "post": -0.312, "description": "-8.0 dB De-emphasis, 0.0 dB Pre-shoot"},
    }

    @classmethod
    def get_preset_taps(cls, preset_name="P7"):
        if preset_name not in cls.PRESETS:
            raise ValueError(f"Unknown preset {preset_name}.")
        p = cls.PRESETS[preset_name]
        c_pre = p["pre"]
        c_post = p["post"]
        c_main = 1.0 - abs(c_pre) - abs(c_post)
        return [c_pre, c_main, c_post]
''',

    "pcie_gen4_serdes/tx/__init__.py": '''from .prbs_generator import PRBSGenerator
from .serializer import Serializer
from .ffe_equalizer import TXFFEEqualizer
from .tx_driver import TXDriver
from .tx_top import TXTop

__all__ = ["PRBSGenerator", "Serializer", "TXFFEEqualizer", "TXDriver", "TXTop"]
''',

    "pcie_gen4_serdes/tx/prbs_generator.py": '''import numpy as np

class PRBSGenerator:
    POLYNOMIALS = {
        7:  (7,),
        15: (15, [15, 14]),
        23: (23, [23, 18]),
        31: (31, [31, 28])
    }

    def __init__(self, order=7, seed=None):
        if order not in self.POLYNOMIALS:
            raise ValueError(f"Unsupported PRBS order {order}.")
        self.order = order
        self.nbits, self.taps = self.POLYNOMIALS[order]
        self.state = (1 << self.nbits) - 1 if seed is None else seed

    def generate(self, num_bits=1000):
        bits = np.zeros(num_bits, dtype=int)
        mask = (1 << self.nbits) - 1
        state = self.state
        for i in range(num_bits):
            feedback = 0
            for tap in self.taps:
                feedback ^= (state >> (self.nbits - tap)) & 1
            bits[i] = state & 1
            state = ((state >> 1) | (feedback << (self.nbits - 1))) & mask
        self.state = state
        return bits
''',

    "pcie_gen4_serdes/tx/serializer.py": '''import numpy as np

class Serializer:
    def __init__(self, bus_width=32):
        self.bus_width = bus_width

    def serialize(self, parallel_words):
        arr = np.asarray(parallel_words)
        if arr.ndim == 1:
            return arr.astype(int)
        return arr.flatten().astype(int)
''',

    "pcie_gen4_serdes/tx/ffe_equalizer.py": '''import numpy as np
from ..config import PCIeGen4Config

class TXFFEEqualizer:
    def __init__(self, preset_name="P7", dac_bits=6, enable_non_idealities=False):
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
''',

    "pcie_gen4_serdes/tx/tx_driver.py": '''import numpy as np
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
''',

    "pcie_gen4_serdes/tx/tx_top.py": '''import numpy as np
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
''',

    "pcie_gen4_serdes/channel/__init__.py": '''from .channel_model import PCIeGen4Channel

__all__ = ["PCIeGen4Channel"]
''',

    "pcie_gen4_serdes/channel/channel_model.py": '''import numpy as np
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
''',

    "pcie_gen4_serdes/rx/__init__.py": '''from .ctle import ContinuousTimeLinearEqualizer
from .vga import VariableGainAmplifier
from .sampler import HighSpeedSampler
from .dfe import AdaptiveDFE
from .cdr import DigitalCDR
from .rx_top import RXTop

__all__ = [
    "ContinuousTimeLinearEqualizer",
    "VariableGainAmplifier",
    "HighSpeedSampler",
    "AdaptiveDFE",
    "DigitalCDR",
    "RXTop"
]
''',

    "pcie_gen4_serdes/rx/ctle.py": '''import numpy as np
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
''',

    "pcie_gen4_serdes/rx/vga.py": '''import numpy as np

class VariableGainAmplifier:
    def __init__(self, target_vpeak=0.4):
        self.target_vpeak = target_vpeak

    def process(self, input_waveform):
        current_vpeak = np.max(np.abs(input_waveform))
        gain_linear = self.target_vpeak / current_vpeak if current_vpeak > 1e-6 else 1.0
        return input_waveform * gain_linear
''',

    "pcie_gen4_serdes/rx/sampler.py": '''import numpy as np

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
                   np.random.choice(, size=len(sampled_v))))
        else:
            bits = np.where(sampled_v >= 0.0, 1, 0)
            
        return bits, sampled_v
''',

    "pcie_gen4_serdes/rx/dfe.py": '''import numpy as np

class AdaptiveDFE:
    def __init__(self, num_taps=2, mu=0.005, v_target=0.35, max_tap_limit=0.15):
        self.num_taps = num_taps
        self.mu = mu
        self.v_target = v_target
        self.max_tap_limit = max_tap_limit
        self.taps = np.zeros(num_taps, dtype=float)
        self.symbols_history = np.zeros(num_taps, dtype=float)

    def process_symbol(self, raw_sample):
        feedback = np.dot(self.taps, self.symbols_history)
        dfe_v = raw_sample - feedback
        decision_symbol = 1.0 if dfe_v >= 0.0 else -1.0
        decision_bit = 1 if dfe_v >= 0.0 else 0
        
        error = dfe_v - (decision_symbol * self.v_target)
        self.taps += self.mu * error * self.symbols_history
        self.taps = np.clip(self.taps, -self.max_tap_limit, self.max_tap_limit)
        
        self.symbols_history = np.roll(self.symbols_history, 1)
        self.symbols_history[0] = decision_symbol
        return dfe_v, decision_bit, error
''',

    "pcie_gen4_serdes/rx/cdr.py": '''import numpy as np

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
''',

    "pcie_gen4_serdes/rx/rx_top.py": '''import numpy as np
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
''',

    "run_nonideal_link_verification.py": '''import numpy as np
import matplotlib.pyplot as plt
from pcie_gen4_serdes.config import PCIeGen4Config
from pcie_gen4_serdes.tx import TXTop
from pcie_gen4_serdes.channel import PCIeGen4Channel
from pcie_gen4_serdes.rx import RXTop

def plot_eye_diagram(time_vec, waveform, title="Eye Diagram", filename="eye.png"):
    ui = PCIeGen4Config.UI
    samples_per_ui = PCIeGen4Config.SAMPLES_PER_UI
    samples_per_eye = 2 * samples_per_ui
    num_eyes = len(waveform) // samples_per_eye
    eye_time = np.linspace(-ui * 1e12, ui * 1e12, samples_per_eye)
    
    plt.figure(figsize=(9, 5))
    for i in range(15, min(num_eyes - 15, 180)):
        segment = waveform[i * samples_per_eye : (i + 1) * samples_per_eye]
        plt.plot(eye_time, segment, color='blue', alpha=0.15, linewidth=0.8)
        
    plt.title(title, fontsize=13, fontweight='bold')
    plt.xlabel("Time (ps)", fontsize=11)
    plt.ylabel("Differential Voltage (V)", fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"[+] Saved Eye Diagram to {filename}")

def main():
    print("="*70)
    print("  PCIe Gen 4 (16 Gbps) NON-IDEAL SerDes Link Verification")
    print("="*70)
    
    num_bits = 2000
    
    # 1. Ideal Baseline
    print("\\n[Part 1] Running IDEAL Link Simulation Baseline...")
    tx_ideal = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=False)
    t_vec, v_tx_ideal, bits, _ = tx_ideal.run(num_bits=num_bits)
    
    channel_ideal = PCIeGen4Channel(loss_db_at_nyquist=28.0, enable_non_idealities=False)
    v_channel_ideal = channel_ideal.transmit(t_vec, v_tx_ideal)
    
    rx_ideal = RXTop(ctle_boost_db=12.0, dfe_taps=2, enable_non_idealities=False)
    _, v_vga_ideal, dfe_v_ideal, rx_bits_ideal, ber_ideal = rx_ideal.run_equalization(t_vec, v_channel_ideal, bits)
    
    plot_eye_diagram(t_vec, v_vga_ideal, 
                     title="IDEAL Link: RX Restored Eye Diagram (Clean Open Eye)", 
                     filename="nonideal_1_ideal_restored_eye.png")

    # 2. Non-Ideal Link Simulation
    print("\\n[Part 2] Running NON-IDEAL Link Simulation...")
    print("  -> Injecting TX Jitter (RJ=0.8ps, SJ=1.5ps, DCD=2%) + BW Limit (12GHz)")
    print("  -> Injecting Channel AWGN Noise / Crosstalk (SNR=25dB)")
    print("  -> Injecting RX AFE Gain Saturation + Sampler Offset (+8mV) + CDR Sampling Jitter")
    
    tx_nonideal = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=True)
    t_vec_ni, v_tx_ni, bits_ni, _ = tx_nonideal.run(num_bits=num_bits)
    
    channel_nonideal = PCIeGen4Channel(loss_db_at_nyquist=28.0, snr_db=25.0, enable_non_idealities=True)
    v_channel_ni = channel_nonideal.transmit(t_vec_ni, v_tx_ni)
    
    rx_nonideal = RXTop(ctle_boost_db=12.0, dfe_taps=2, enable_non_idealities=True)
    _, v_vga_ni, dfe_v_ni, rx_bits_ni, ber_ni = rx_nonideal.run_equalization(t_vec_ni, v_channel_ni, bits_ni)
    
    plot_eye_diagram(t_vec_ni, v_vga_ni, 
                     title="NON-IDEAL Link: RX Restored Eye Diagram (With Jitter, Noise & Offset)", 
                     filename="nonideal_2_nonideal_restored_eye.png")

    # 3. Summary
    print("\\n" + "="*70)
    print("  NON-IDEAL VS IDEAL PERFORMANCE COMPARISON SUMMARY")
    print("="*70)
    print(f"  Ideal Link BER     : {ber_ideal:.6e} (Errors: {int(ber_ideal * (num_bits - 100))})")
    print(f"  Non-Ideal Link BER : {ber_ni:.6e} (Errors: {int(ber_ni * (num_bits - 100))})")
    print(f"  Non-Ideal DFE h1   : {rx_nonideal.dfe.taps[0]:.4f}")
    print(f"  Non-Ideal DFE h2   : {rx_nonideal.dfe.taps:.4f}")
    print("="*70)
    
    if ber_ni < 1e-3:
        print("\\n[SUCCESS] Non-Ideal Link Achieved Low BER / Error-Free Restoration under Physical Impairments!")
    else:
        print(f"\\n[NOTICE] Non-Ideal Link BER = {ber_ni:.4f} (Reflects Physical Margin Degradation)")

if __name__ == "__main__":
    main()
'''
}

# 執行寫入檔名
for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("[+] setup_project_nonideal.py 自動建立完成！")