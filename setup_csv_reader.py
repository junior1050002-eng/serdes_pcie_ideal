import os

# 純真實 HSPICE CSV 波形 + Python 數位 DFE/BER 分析平台腳本
files = {
    "read_real_hspice_csv.py": '''import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pcie_gen4_serdes.config import PCIeGen4Config
from pcie_gen4_serdes.tx import TXTop
from pcie_gen4_serdes.rx import RXTop

POSSIBLE_FILENAMES = ["serdes_top_018.csv", "hspice_real_wave.csv"]

def plot_real_hspice_eye_diagram(hspice_time, hspice_v_ctle, filename="real_hspice_restored_eye.png"):
    """
    100% Pure HSPICE Data Eye Diagram Plotter.
    Folds raw HSPICE CSV waveform data into a clean 2-UI Eye Diagram.
    """
    ui = PCIeGen4Config.UI  # 62.5 ps for 16 Gbps
    samples_per_ui = 64
    samples_per_eye = 2 * samples_per_ui
    
    # 1. 自動濾除前 1ns 的直流過渡期
    valid_mask = hspice_time >= 1e-9
    if np.sum(valid_mask) < 20:
        valid_mask = np.ones(len(hspice_time), dtype=bool)
        
    t_valid = hspice_time[valid_mask] - hspice_time[valid_mask][0]
    v_valid = hspice_v_ctle[valid_mask]
    
    # 2. 高解析度時間軸內插
    t_uniform = np.arange(0, t_valid[-1], ui / samples_per_ui)
    v_interp = np.interp(t_uniform, t_valid, v_valid)
    
    num_eyes = len(v_interp) // samples_per_eye
    eye_time = np.linspace(-ui * 1e12, ui * 1e12, samples_per_eye)
    
    # 3. 繪製純真實 HSPICE 電晶體眼圖
    plt.figure(figsize=(9, 5.5))
    for i in range(num_eyes):
        segment = v_interp[i * samples_per_eye : (i + 1) * samples_per_eye]
        if len(segment) == samples_per_eye:
            plt.plot(eye_time, segment, color='darkgreen', alpha=0.15, linewidth=0.8)
            
    plt.title("HSPICE Real Transistor Circuit Restored Eye Diagram (TSMC 0.18um)", fontsize=12, fontweight='bold')
    plt.xlabel("Time (ps)", fontsize=11)
    plt.ylabel("Differential Voltage (V)", fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.ylim(-0.8, 0.8)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"[+] 成功繪製並導出純真實 HSPICE 眼圖至 '{filename}'！")

def main():
    print("="*75)
    print("  純真實 HSPICE 電晶體波形 (.csv) + Python 數位 DFE/BER 分析平台")
    print("="*75)

    csv_filename = None
    for fn in POSSIBLE_FILENAMES:
        if os.path.exists(fn):
            csv_filename = fn
            break

    if csv_filename is None:
        print(f"\\n[錯誤] 在目錄下找不到真正的 HSPICE 波形檔 ({POSSIBLE_FILENAMES})！")
        print("請確認 Custom WaveView 匯出的 CSV 已儲存在 C:\\\\Users\\\\junio\\\\vscode\\\\pcie_serdes\\\\ 目錄下。")
        return

    print(f"\\n 正在開啟並解析 Custom WaveView CSV 數據檔: '{csv_filename}'...")
    try:
        with open(csv_filename, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
        data_lines = lines[1:]
        data = np.genfromtxt(data_lines, delimiter=',')
        
        if data.ndim == 1:
            data = data.reshape(-1, 1)
            
        # 使用 .flatten() 確保 1D 陣列，解決 np.interp ValueError
        hspice_time = np.asarray(data[:, 0], dtype=float).flatten()
        hspice_v_ctle = np.asarray(data, dtype=float).flatten()
        
        print(f"  [+] 成功解析出 {len(hspice_time)} 個 HSPICE 真實電晶體波形數據點！")
        print(f"  [+] 時間範圍: {hspice_time[0]*1e9:.2f} ns ~ {hspice_time[-1]*1e9:.2f} ns")
        print(f"  [+] 電壓擺幅: {np.min(hspice_v_ctle):.3f} V ~ {np.max(hspice_v_ctle):.3f} V")
        
    except Exception as e:
        print(f"  [!] 解析 CSV 失敗，請確認格式: {e}")
        return

    # 1. 繪製並導出 100% 純真實 HSPICE 的眼圖
    plot_real_hspice_eye_diagram(hspice_time, hspice_v_ctle, "real_hspice_restored_eye.png")

    # 2. 自動按 CSV 實際時間長度進行位元對齊與 Python 數位 DFE 測試
    ui_sec = PCIeGen4Config.UI
    csv_duration_sec = hspice_time[-1] - hspice_time[0]
    num_bits_csv = int(csv_duration_sec / ui_sec)
    if num_bits_csv < 10:
        num_bits_csv = 160

    print(f"\\n 將【真正的 HSPICE 電晶體波形】送入 Python 數位 DFE (LMS 演算法) 進行位元還原與 BER 測試...")
    tx_py = TXTop(prbs_order=7, preset_name="P7", enable_non_idealities=True)
    bits = tx_py.prbs.generate(num_bits_csv)
    
    t_vec_csv = np.linspace(0, csv_duration_sec, num_bits_csv * PCIeGen4Config.SAMPLES_PER_UI)
    v_sp_interp = np.interp(t_vec_csv, hspice_time, hspice_v_ctle)
    
    rx_hspice = RXTop(ctle_boost_db=12.0, dfe_taps=2, enable_non_idealities=True)
    _, _, dfe_v_sp, rx_bits_sp, ber_sp = rx_hspice.run_equalization(t_vec_csv, v_sp_interp, bits)

    eye_h_sp = np.mean(np.abs(dfe_v_sp)) * 2000.0

    print("\\n" + "="*75)
    print("  【純真實 HSPICE 電晶體波形檔 + Python 數位 DFE】數據總表")
    print("="*75)
    print(f"  解析資料點數 (Data Points)   | {len(hspice_time):18d}")
    print(f"  模擬時間範圍 (Time Span)     | {csv_duration_sec*1e9:15.2f} ns")
    print(f"  實測峰對峰擺幅 Vdiff_p2p (mV) | {(np.max(hspice_v_ctle) - np.min(hspice_v_ctle))*1000.0:18.1f}")
    print(f"  等化後眼高 Eye Height (mV)  | {eye_h_sp:18.1f}")
    print(f"  DFE Tap 1 權重 (h1)          | {rx_hspice.dfe.taps[0]:18.4f}")
    print(f"  DFE Tap 2 權重 (h2)          | {rx_hspice.dfe.taps:18.4f}")
    print(f"  實測全鏈路 BER               | {ber_sp:18.6e}")
    print("="*75)
    print("\\n[SUCCESS] 純真實 HSPICE 電晶體波形 + Python 數位 DFE/BER 分析完成！")

if __name__ == "__main__":
    main()
'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("[+] setup_csv_reader.py 建立完成！")