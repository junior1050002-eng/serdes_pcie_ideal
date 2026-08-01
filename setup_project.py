import os

# 專案檔案結構與原始碼內容定義
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
        7:  (7, [7, 6]),
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
''',

    "pcie_gen4_serdes/tx/tx_driver.py": '''import numpy as np
from scipy.signal import butter, lfilter
from ..config import PCIeGen4Config

class TXDriver:
    def __init__(self, bandwidth_hz=16e9, rj_ps=0.5, sj_amp_ps=1.5, sj_freq_hz=100e6, dcd_percent=2.0, v_swing=PCIeGen4Config.V_SWING_P2P, enable_non_idealities=False):
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
            
        if self.bandwidth_hz is not None and self.bandwidth_hz > 0:
            fs = PCIeGen4Config.FS
            nyq = 0.5 * fs
            normal_cutoff = self.bandwidth_hz / nyq
            b, a = butter(1, normal_cutoff, btype='low', analog=False)
            tx_waveform = lfilter(b, a, raw_waveform)
        else:
            tx_waveform = raw_waveform

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

    "run_tx_verification.py": '''import numpy as np
import matplotlib.pyplot as plt
from pcie_gen4_serdes.config import PCIeGen4Config
from pcie_gen4_serdes.tx import TXTop

def plot_eye_diagram(time_vec, waveform, title="TX Output Eye Diagram", filename="tx_eye.png"):
    ui = PCIeGen4Config.UI
    samples_per_ui = PCIeGen4Config.SAMPLES_PER_UI
    samples_per_eye = 2 * samples_per_ui
    num_eyes = len(waveform) // samples_per_eye
    eye_time = np.linspace(-ui * 1e12, ui * 1e12, samples_per_eye)
    
    plt.figure(figsize=(9, 5))
    for i in range(10, min(num_eyes - 10, 150)):
        segment = waveform[i * samples_per_eye : (i + 1) * samples_per_eye]
        plt.plot(eye_time, segment, color='blue', alpha=0.15, linewidth=0.8)
        
    plt.title(title, fontsize=13, fontweight='bold')
    plt.xlabel("Time (ps)", fontsize=11)
    plt.ylabel("Differential Voltage (V)", fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.ylim(-0.6, 0.6)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"[+] Saved Eye Diagram to {filename}")

def main():
    print("="*60)
    print("  PCIe Gen 4 (16 Gbps) SerDes TX Standalone Verification")
    print("="*60)
    
    print("\\n[1] Running Ideal TX Simulation (Preset P4 - Flat)...")
    tx_ideal_p4 = TXTop(prbs_order=7, preset_name="P4", enable_non_idealities=False)
    t_ideal_p4, v_ideal_p4, _, _ = tx_ideal_p4.run(num_bits=2000)
    plot_eye_diagram(t_ideal_p4, v_ideal_p4, title="PCIe Gen 4 Ideal TX Output (Preset P4: Flat)", filename="tx_eye_ideal_p4.png")

    print("\\n[2] Running Ideal TX Simulation (Preset P7 - Equalized)...")
    tx_ideal_p7 = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=False)
    t_ideal_p7, v_ideal_p7, _, _ = tx_ideal_p7.run(num_bits=2000)
    plot_eye_diagram(t_ideal_p7, v_ideal_p7, title="PCIe Gen 4 Ideal TX Output (Preset P7: -6dB De-emphasis, +3.5dB Pre-shoot)", filename="tx_eye_ideal_p7.png")

    print("\\n[3] Running Non-Ideal TX Simulation (Preset P7 + RJ/SJ/DCD)...")
    tx_nonideal = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=True)
    t_nonideal, v_nonideal, _, _ = tx_nonideal.run(num_bits=2000)
    plot_eye_diagram(t_nonideal, v_nonideal, title="PCIe Gen 4 Non-Ideal TX Output (Preset P7 + RJ/SJ/DCD)", filename="tx_eye_nonideal_p7.png")

    print("\\n[+] TX Standalone Verification Completed Successfully!")

if __name__ == "__main__":
    main()
'''
}

# 執行自動建立檔名與資料夾
for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("[+] 專案目錄與所有 .py 檔案已成功自動建立完成！")