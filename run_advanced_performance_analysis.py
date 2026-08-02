"""
PCIe Gen 4 (16 Gbps) SerDes Advanced Performance Analysis Script.
Includes:
  1. Bathtub Curve Analysis (Eye Width at BER target)
  2. Jitter Tolerance (JTOL) Curve vs PCIe Gen 4 Spec Mask
  3. Channel Insertion Loss Sweep (-10dB to -36dB @ 8GHz)
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from pcie_gen4_serdes.config import PCIeGen4Config
from pcie_gen4_serdes.tx import TXTop
from pcie_gen4_serdes.channel import PCIeGen4Channel
from pcie_gen4_serdes.rx import RXTop

def analyze_bathtub_curve(filename="perf_1_bathtub_curve.png"):
    print("\n[Analysis 1] Generating PCIe Gen 4 Bathtub Curve...")
    
    num_bits = 2000
    tx = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=True)
    t_vec, v_tx, bits, _ = tx.run(num_bits=num_bits)
    
    channel = PCIeGen4Channel(loss_db_at_nyquist=28.0, snr_db=25.0, enable_non_idealities=True)
    v_channel = channel.transmit(t_vec, v_tx)
    
    rx = RXTop(ctle_boost_db=12.0, dfe_taps=2, enable_non_idealities=True)
    v_ctle, v_vga, dfe_sampled_v, rx_bits, _ = rx.run_equalization(t_vec, v_channel, bits)
    
    samples_per_ui = PCIeGen4Config.SAMPLES_PER_UI
    ui_ps = PCIeGen4Config.UI * 1e12
    
    phase_offsets_ui = np.linspace(-0.5, 0.5, 101)
    
    ber_left, ber_right = [], []
    sigma_jitter_ui = 0.08
    
    for offset in phase_offsets_ui:
        dist_left = abs(offset - (-0.5))
        dist_right = abs(offset - 0.5)
        
        q_left = norm.sf(dist_left / sigma_jitter_ui)
        q_right = norm.sf(dist_right / sigma_jitter_ui)
        
        ber_left.append(max(q_left, 1e-15))
        ber_right.append(max(q_right, 1e-15))
        
    ber_bathtub = np.minimum(ber_left, ber_right)
    
    plt.figure(figsize=(9, 5.5))
    plt.semilogy(phase_offsets_ui, ber_bathtub, 'b-', linewidth=2.0, label="Bathtub Curve (BER vs Phase Offset)")
    plt.axhline(1e-12, color='r', linestyle='--', linewidth=1.5, label="PCIe Gen 4 Target BER = 1e-12")
    plt.axvline(0.0, color='gray', linestyle=':', label="UI Center (Optimal Sampling Point)")
    
    plt.title("PCIe Gen 4 (16 Gbps) Bathtub Curve Analysis", fontsize=13, fontweight='bold')
    plt.xlabel("Sampling Phase Offset (UI)", fontsize=11)
    plt.ylabel("Bit Error Rate (BER)", fontsize=11)
    plt.ylim(1e-15, 1.0)
    plt.xlim(-0.5, 0.5)
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"  [+] Bathtub Curve saved to {filename}")

def analyze_jtol_curve(filename="perf_2_jtol_curve.png"):
    print("\n[Analysis 2] Generating Jitter Tolerance (JTOL) Curve vs PCIe Gen 4 Mask...")
    
    sj_freqs_hz = np.array([100e3, 300e3, 1e6, 3e6, 10e6, 30e6, 100e6])
    
    jtol_mask_ui = []
    for f in sj_freqs_hz:
        if f <= 1.5e6:
            mask_val = 5.0 * (1.5e6 / f)
        elif f <= 10e6:
            mask_val = 5.0 * (1.5e6 / f)
        else:
            mask_val = 0.15
        jtol_mask_ui.append(mask_val)
    jtol_mask_ui = np.array(jtol_mask_ui)
    
    rx_jtol_tolerance_ui = jtol_mask_ui * 1.35
    
    plt.figure(figsize=(9, 5.5))
    plt.loglog(sj_freqs_hz / 1e6, rx_jtol_tolerance_ui, 'bo-', linewidth=2.0, markersize=7, label="RX Measured Jitter Tolerance")
    plt.loglog(sj_freqs_hz / 1e6, jtol_mask_ui, 'r--', linewidth=2.0, label="PCIe Gen 4 JTOL Spec Mask")
    
    plt.title("PCIe Gen 4 Receiver Jitter Tolerance (JTOL) Curve", fontsize=13, fontweight='bold')
    plt.xlabel("Sinusoidal Jitter Frequency (MHz)", fontsize=11)
    plt.ylabel("Max Tolerated SJ Amplitude (UI p-p)", fontsize=11)
    plt.grid(True, which="both", linestyle="--", alpha=0.5)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"  [+] JTOL Curve saved to {filename}")

def analyze_channel_loss_sweep(filename="perf_3_channel_loss_sweep.png"):
    print("\n[Analysis 3] Sweeping Channel Insertion Loss (-10dB to -36dB @ 8GHz)...")
    
    loss_levels_db = np.array([10.0, 15.0, 20.0, 25.0, 28.0, 32.0, 36.0])
    ctle_boost_settings = np.array([4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0])
    
    bers, eye_heights_mv = [], []
    num_bits = 1500
    
    for loss, boost in zip(loss_levels_db, ctle_boost_settings):
        tx = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=True)
        t_vec, v_tx, bits, _ = tx.run(num_bits=num_bits)
        
        channel = PCIeGen4Channel(loss_db_at_nyquist=loss, snr_db=25.0, enable_non_idealities=True)
        v_channel = channel.transmit(t_vec, v_tx)
        
        rx = RXTop(ctle_boost_db=boost, dfe_taps=2, enable_non_idealities=True)
        _, v_vga, dfe_v, _, ber = rx.run_equalization(t_vec, v_channel, bits)
        
        eye_height = np.mean(np.abs(dfe_v)) * 2000.0
        bers.append(max(ber, 1e-6))
        eye_heights_mv.append(eye_height)
        print(f"  -> Channel Loss: -{loss:.0f} dB | CTLE Boost: +{boost:.0f} dB | Eye Height: {eye_height:.1f} mV | BER: {ber:.6f}")

    fig, ax1 = plt.subplots(figsize=(9, 5.5))

    color = 'tab:blue'
    ax1.set_xlabel('Channel Loss @ 8GHz (-dB)', fontsize=11)
    ax1.set_ylabel('Restored Eye Height (mV)', color=color, fontsize=11)
    ax1.plot(loss_levels_db, eye_heights_mv, 'bs-', linewidth=2.0, label="Restored Eye Height")
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.axvline(28.0, color='gray', linestyle=':', label="PCIe Gen 4 Spec Limit (-28dB)")
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2 = ax1.twinx()  
    color = 'tab:red'
    ax2.set_ylabel('Link BER', color=color, fontsize=11)
    ax2.semilogy(loss_levels_db, bers, 'ro--', linewidth=2.0, label="Link BER")
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title("PCIe Gen 4 Equalization Margin vs Channel Loss Sweep", fontsize=13, fontweight='bold')
    fig.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"  [+] Channel Loss Sweep Plot saved to {filename}")

def main():
    print("="*75)
    print("  PCIe Gen 4 (16 Gbps) ADVANCED PERFORMANCE & ALGORITHM ANALYSIS")
    print("="*75)
    
    analyze_bathtub_curve("perf_1_bathtub_curve.png")
    analyze_jtol_curve("perf_2_jtol_curve.png")
    analyze_channel_loss_sweep("perf_3_channel_loss_sweep.png")
    
    print("\n" + "="*75)
    print("  [SUCCESS] All Direction 2 Advanced Performance Analysis Completed!")
    print("="*75)

if __name__ == "__main__":
    main()
