import numpy as np
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
    print("="*65)
    print("  PCIe Gen 4 (16 Gbps) Full SerDes Link (TX -> Channel -> RX)")
    print("="*65)
    
    num_bits = 2000
    
    print("\n[Step 1] Running TX Simulation (Preset P7)...")
    tx = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=False)
    t_vec, v_tx, bits, _ = tx.run(num_bits=num_bits)
    
    print("\n[Step 2] Transmitting through Lossy Board Trace (-28 dB Loss)...")
    channel = PCIeGen4Channel(loss_db_at_nyquist=28.0)
    v_channel = channel.transmit(t_vec, v_tx)
    plot_eye_diagram(t_vec, v_channel, 
                     title="PCIe Gen 4 Channel Output Eye Diagram (-28dB Loss @ 8GHz - CLOSED EYE)", 
                     filename="link_1_channel_output_closed_eye.png")
    
    print("\n[Step 3] Running RX Equalization (CTLE + VGA + DFE)...")
    rx = RXTop(ctle_boost_db=12.0, dfe_taps=2)
    v_ctle, v_vga, dfe_sampled_v, rx_bits, ber = rx.run_equalization(t_vec, v_channel, bits)
    
    plot_eye_diagram(t_vec, v_vga, 
                     title="PCIe Gen 4 RX CTLE+VGA Restored Eye Diagram (OPEN EYE)", 
                     filename="link_2_rx_ctle_restored_open_eye.png")
    
    print("\n[Step 4] DFE LMS Convergence & BER Performance Results:")
    print(f"  -> DFE Tap 1 Weight (h1): {rx.dfe.taps[0]:.4f}")
    print(f"  -> DFE Tap 2 Weight (h2): {rx.dfe.taps[1]:.4f}")
    print(f"  -> Link Bit Error Rate (BER): {ber:.6e} (Bit Error Count: {int(ber * (num_bits - 100))})")
    
    if ber == 0.0:
        print("\n[SUCCESS] PCIe Gen 4 Link Achieved Zero BER! Equalization Successfully Restored Signal!")
    else:
        print(f"\n[WARNING] Link BER = {ber}")

if __name__ == "__main__":
    main()
