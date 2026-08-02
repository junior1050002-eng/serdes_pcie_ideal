"""
HSPICE PWL Waveform Exporter Script.
Exports Python PCIe Gen 4 PRBS7 / Preset P7 waveform into HSPICE .pwl format.
"""

import numpy as np
from pcie_gen4_serdes.tx import TXTop

def export_pwl_file(time_vec, tx_waveform, filename="tx_output_p7.pwl"):
    print(f"\n[Exporter] Exporting {len(time_vec)} time-domain points to HSPICE PWL file: '{filename}'...")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("* PCIe Gen 4 (16 Gbps) TX Output Piecewise Linear (PWL) Waveform for HSPICE\n")
        f.write("* Format: Time(s) Differential_Voltage(V)\n")
        for t, v in zip(time_vec, tx_waveform):
            f.write(f"{t:.6e} {v:.6f}\n")
            
    print(f"  [+] HSPICE PWL file successfully saved to '{filename}'!")

def main():
    tx = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=True)
    time_vec, tx_waveform, _, _ = tx.run(num_bits=1000)
    export_pwl_file(time_vec, tx_waveform, "tx_output_p7.pwl")

if __name__ == "__main__":
    main()
