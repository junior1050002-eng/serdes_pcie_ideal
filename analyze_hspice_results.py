"""
Master Real HSPICE Data Analyzer & Plotter.
Parses CSV outputs exported from 5 HSPICE Netlists:
  1. cml_driver_018.sp            -> cml_driver.csv
  2. ctle_018.sp                  -> ctle_ac.csv
  3. sampler_018.sp               -> sampler.csv
  4. pcie_gen4_hspice_template.sp -> hspice_real_wave.csv
  5. serdes_top_018.sp            -> serdes_top_018.csv
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pcie_gen4_serdes.config import PCIeGen4Config

def parse_waveview_csv(csv_path):
    if not os.path.exists(csv_path):
        return None, None, None
        
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
    if len(lines) < 2:
        return None, None, None
        
    header = lines[0]
    data_lines = lines[1:]
    data = np.genfromtxt(data_lines, delimiter=',')
    
    if data.ndim == 1:
        data = data.reshape(-1, 1)
        
    time_vec = np.asarray(data[:, 0], dtype=float).flatten()
    col_names = [c.strip() for c in header.split(',')]
    
    signals = {}
    num_cols = data.shape[1]
    for idx in range(1, num_cols):
        col_name = col_names[idx] if idx < len(col_names) else f"Signal_{idx}"
        signals[col_name] = np.asarray(data[:, idx], dtype=float).flatten()
        
    return time_vec, signals, col_names

def plot_real_eye(time_vec, signal_vec, period_ps=400, title="Real HSPICE Eye Diagram", filename="eye.png"):
    ui_sec = period_ps * 1e-12
    samples_per_ui = 64
    samples_per_eye = 2 * samples_per_ui
    
    t_start_cutoff = time_vec[0] + (time_vec[-1] - time_vec[0]) * 0.05
    valid_mask = time_vec >= t_start_cutoff
    if np.sum(valid_mask) < 50:
        valid_mask = np.ones(len(time_vec), dtype=bool)
        
    t_valid = time_vec[valid_mask] - time_vec[valid_mask][0]
    v_valid = signal_vec[valid_mask]
    
    t_uniform = np.arange(0, t_valid[-1], ui_sec / samples_per_ui)
    v_interp = np.interp(t_uniform, t_valid, v_valid)
    
    num_eyes = len(v_interp) // samples_per_eye
    eye_time = np.linspace(-period_ps, period_ps, samples_per_eye)
    
    plt.figure(figsize=(9, 5.5))
    for i in range(num_eyes):
        segment = v_interp[i * samples_per_eye : (i + 1) * samples_per_eye]
        if len(segment) == samples_per_eye:
            plt.plot(eye_time, segment, color='darkgreen', alpha=0.15, linewidth=0.8)
            
    plt.title(title, fontsize=12, fontweight='bold')
    plt.xlabel("Time (ps)", fontsize=11)
    plt.ylabel("Differential Voltage (V)", fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.ylim(-0.8, 0.8)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    
    v_peak_pos = np.max(v_valid)
    v_peak_neg = np.min(v_valid)
    eye_height_mv = (v_peak_pos - v_peak_neg) * 1000.0
    print(f"  [+] 成功繪製並存檔眼圖: '{filename}' (實測擺幅: {eye_height_mv:.1f} mVp-p)")

def main():
    print("="*80)
    print("  5 大 HSPICE 電路實測波形與數據全方位分析總平台")
    print("="*80)
    
    # 1. cml_driver_018.sp -> cml_driver.csv
    print("\n[1/5] 分析 cml_driver_018.sp 實測結果 (cml_driver.csv)...")
    t, sigs, _ = parse_waveview_csv("cml_driver.csv")
    if t is not None:
        v_cml = sigs[list(sigs.keys())[0]]
        swing_mv = (np.max(v_cml) - np.min(v_cml)) * 1000.0
        print(f"  [+] 實測 CML 差動擺幅 Vod_p2p: {swing_mv:.1f} mVp-p")
        plot_real_eye(t, v_cml, period_ps=400, title="TX CML Driver Real Eye Diagram (2.5 Gbps)", filename="real_eye_1_cml_driver.png")
    else:
        print("  [!] 提示: 未找到 'cml_driver.csv'。可在 WaveView 載入 cml_driver_018.tr0 匯出 v(out_p, out_n)。")

    # 2. ctle_018.sp -> ctle_ac.csv
    print("\n[2/5] 分析 ctle_018.sp 實測結果 (ctle_ac.csv)...")
    t_ac, sigs_ac, _ = parse_waveview_csv("ctle_ac.csv")
    if t_ac is not None:
        v_ac = sigs_ac[list(sigs_ac.keys())[0]]
        plt.figure(figsize=(8, 4.5))
        plt.semilogx(t_ac / 1e9, v_ac, 'g-', linewidth=2.0)
        plt.title("RX CTLE Real HSPICE AC Frequency Response (Bode Plot)", fontsize=12, fontweight='bold')
        plt.xlabel("Frequency (GHz)", fontsize=11)
        plt.ylabel("Gain (dB)", fontsize=11)
        plt.grid(True, which="both", linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig("real_bode_ctle_ac.png", dpi=150)
        plt.close()
        print("  [+] 成功繪製並存檔 CTLE Bode Plot: 'real_bode_ctle_ac.png'")
    else:
        print("  [!] 提示: 未找到 'ctle_ac.csv'。可在 WaveView 載入 ctle_018.ac0 匯出 vdb(out_p, out_n)。")

    # 3. sampler_018.sp -> sampler.csv
    print("\n[3/5] 分析 sampler_018.sp 實測結果 (sampler.csv)...")
    t_sa, sigs_sa, _ = parse_waveview_csv("sampler.csv")
    if t_sa is not None:
        print(f"  [+] 成功解析 Sampler 採樣器波形點數: {len(t_sa)}")
    else:
        print("  [!] 提示: 未找到 'sampler.csv'。可在 WaveView 載入 sampler_018.tr0 匯出 v(clk), v(out_p), v(out_n)。")

    # 4. pcie_gen4_hspice_netlist_template.sp -> hspice_real_wave.csv
    print("\n[4/5] 分析 pcie_gen4_hspice_netlist_template.sp 實測結果 (hspice_real_wave.csv)...")
    t_tmpl, sigs_tmpl, _ = parse_waveview_csv("hspice_real_wave.csv")
    if t_tmpl is not None:
        v_tmpl = sigs_tmpl[list(sigs_tmpl.keys())[0]]
        plot_real_eye(t_tmpl, v_tmpl, period_ps=62.5, title="RX CTLE Template Eye Diagram (16 Gbps)", filename="real_eye_template.png")
    else:
        print("  [!] 提示: 未找到 'hspice_real_wave.csv'。")

    # 5. serdes_top_018.sp -> serdes_top_018.csv
    print("\n[5/5] 分析 serdes_top_018.sp 全鏈路實測結果 (serdes_top_018.csv)...")
    fn = "serdes_top_018.csv" if os.path.exists("serdes_top_018.csv") else "serdes_top.csv"
    t_top, sigs_top, _ = parse_waveview_csv(fn)
    if t_top is not None:
        v_top = sigs_top[list(sigs_top.keys())[0]]
        swing_top = (np.max(v_top) - np.min(v_top)) * 1000.0
        print(f"  [+] 成功解析 Top-Level 全鏈路數據點數: {len(t_top)}")
        print(f"  [+] 全鏈路 0.18um 頂層實測擺幅: {swing_top:.1f} mVp-p")
        plot_real_eye(t_top, v_top, period_ps=62.5, title="Full SerDes Top-Level Real Eye Diagram (PCIe Gen 4)", filename="real_eye_serdes_top.png")
    else:
        print("  [!] 提示: 未找到 'serdes_top_018.csv'。可在 WaveView 載入 serdes_top_018.tr0 匯出 v(rx_ctle_p, rx_ctle_n)。")

    print("\n" + "="*80)
    print("  分析完成！所有匯出的真實 HSPICE CSV 資料已處理完畢。")
    print("="*80)

if __name__ == "__main__":
    main()
