import numpy as np
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
    
    print("\n Running Ideal TX Simulation (Preset P4 - Flat)...")
    tx_ideal_p4 = TXTop(prbs_order=7, preset_name="P4", enable_non_idealities=False)
    t_ideal_p4, v_ideal_p4, _, _ = tx_ideal_p4.run(num_bits=2000)
    plot_eye_diagram(t_ideal_p4, v_ideal_p4, title="PCIe Gen 4 Ideal TX Output (Preset P4: Flat)", filename="tx_eye_ideal_p4.png")

    print("\n Running Ideal TX Simulation (Preset P7 - Equalized)...")
    tx_ideal_p7 = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=False)
    t_ideal_p7, v_ideal_p7, _, _ = tx_ideal_p7.run(num_bits=2000)
    plot_eye_diagram(t_ideal_p7, v_ideal_p7, title="PCIe Gen 4 Ideal TX Output (Preset P7: -6dB De-emphasis, +3.5dB Pre-shoot)", filename="tx_eye_ideal_p7.png")

    print("\n Running Non-Ideal TX Simulation (Preset P7 + RJ/SJ/DCD)...")
    tx_nonideal = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=True)
    t_nonideal, v_nonideal, _, _ = tx_nonideal.run(num_bits=2000)
    plot_eye_diagram(t_nonideal, v_nonideal, title="PCIe Gen 4 Non-Ideal TX Output (Preset P7 + RJ/SJ/DCD)", filename="tx_eye_nonideal_p7.png")

    print("\n[+] TX Standalone Verification Completed Successfully!")

if __name__ == "__main__":
    main()
