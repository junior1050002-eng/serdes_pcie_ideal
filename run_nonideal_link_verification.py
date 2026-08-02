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
    print("="*70)
    print("  PCIe Gen 4 (16 Gbps) NON-IDEAL SerDes Link Verification")
    print("="*70)
    
    num_bits = 2000
    
    # 1. Ideal Baseline
    print("\n[Part 1] Running IDEAL Link Simulation Baseline...")
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
    print("\n[Part 2] Running NON-IDEAL Link Simulation...")
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
    print("\n" + "="*70)
    print("  NON-IDEAL VS IDEAL PERFORMANCE COMPARISON SUMMARY")
    print("="*70)
    print(f"  Ideal Link BER     : {ber_ideal:.6e} (Errors: {int(ber_ideal * (num_bits - 100))})")
    print(f"  Non-Ideal Link BER : {ber_ni:.6e} (Errors: {int(ber_ni * (num_bits - 100))})")
    print(f"  Non-Ideal DFE h1   : {rx_nonideal.dfe.taps[0]:.4f}")
    print(f"  Non-Ideal DFE h2   : {rx_nonideal.dfe.taps[1]:.4f}")
    print("="*70)
    
    if ber_ni < 1e-3:
        print("\n[SUCCESS] Non-Ideal Link Achieved Low BER / Error-Free Restoration under Physical Impairments!")
    else:
        print(f"\n[NOTICE] Non-Ideal Link BER = {ber_ni:.4f} (Reflects Physical Margin Degradation)")

if __name__ == "__main__":
    main()
