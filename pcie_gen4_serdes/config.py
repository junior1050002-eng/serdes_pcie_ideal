"""
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
