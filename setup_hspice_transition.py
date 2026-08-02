import os

# PCIe Gen 4 SerDes HSPICE 對接工具建立腳本
files = {
    "export_hspice_pwl.py": '''"""
HSPICE PWL Waveform Exporter Script.
Exports Python PCIe Gen 4 PRBS7 / Preset P7 waveform into HSPICE .pwl format.
"""

import numpy as np
from pcie_gen4_serdes.tx import TXTop

def export_pwl_file(time_vec, tx_waveform, filename="tx_output_p7.pwl"):
    print(f"\\n[Exporter] Exporting {len(time_vec)} time-domain points to HSPICE PWL file: '{filename}'...")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("* PCIe Gen 4 (16 Gbps) TX Output Piecewise Linear (PWL) Waveform for HSPICE\\n")
        f.write("* Format: Time(s) Differential_Voltage(V)\\n")
        for t, v in zip(time_vec, tx_waveform):
            f.write(f"{t:.6e} {v:.6f}\\n")
            
    print(f"  [+] HSPICE PWL file successfully saved to '{filename}'!")

def main():
    tx = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=True)
    time_vec, tx_waveform, _, _ = tx.run(num_bits=1000)
    export_pwl_file(time_vec, tx_waveform, "tx_output_p7.pwl")

if __name__ == "__main__":
    main()
''',

    "pcie_gen4_hspice_netlist_template.sp": '''* =======================================================================
* PCIe Gen 4 (16 Gbps) SerDes Physical Layer Circuit Testbench Template
* Technology: TSMC / Generic CMOS Process
* =======================================================================

* 1. Include Semiconductor Process PDK (.lib)
.lib 'tsmc28nm.lib' tt
.option post=2 probe=1 ingold=2

* 2. Global Power & Clock Sources
VDD VDD 0 DC 1.0V
VSS VSS 0 DC 0.0V

* 3. Import PWL Waveform Exported from Python (tx_output_p7.pwl)
V_TX_IN IN_P IN_N PWL file='tx_output_p7.pwl'

* 4. RX On-Chip Termination & ESD Parasitics (200fF ESD + 50 Ohm Termination)
R_TERM_P IN_P V_BIAS 50.0
R_TERM_N IN_N V_BIAS 50.0
V_BIAS   V_BIAS 0 DC 0.5V
C_ESD_P  IN_P 0 200fF
C_ESD_N  IN_N 0 200fF

* 5. RX CTLE (Source-Degenerated Differential Pair Topology)
* CTLE Transistors: M1, M2 (Input Pair)
* Source Degeneration: Rs = 200 Ohm, Cs = 150 fF (Achieves +12dB Boost @ 8GHz)
* Load Resistors: R_L1, R_L2 = 1k Ohm
X_CTLE IN_P IN_N OUT_CTLE_P OUT_CTLE_N VDD VSS CTLE_BLOCK

.subckt CTLE_BLOCK vin_p vin_n vout_p vout_n vdd vss
M1 vout_n vin_p node_a vss nch W=10u L=0.03u
M2 vout_p vin_n node_b vss nch W=10u L=0.03u
Rs node_a node_b 200
Cs node_a node_b 150fF
RL1 vdd vout_p 1k
RL2 vdd vout_n 1k
Iss node_a vss DC 1mA
.ends CTLE_BLOCK

* 6. Simulation Analysis Commands
* AC Frequency Sweep Analysis (Check CTLE +12dB Boost @ 8GHz)
.ac dec 20 100MHz 20GHz

* Transient Eye Diagram Analysis
.tran 0.1ps 125ns

* Eye Diagram Generation Syntax
.eye_diagram tstart=10ns tstop=125ns period=62.5ps
.end
'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("[+] setup_hspice_transition.py 建立完成！")