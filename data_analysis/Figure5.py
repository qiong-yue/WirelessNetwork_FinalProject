import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 1. 基礎設定與檔案路徑 
BASE_DIR = Path(__file__).resolve().parent

# 設定輸入檔案路徑 (對應您的專案目錄結構)
files = {
    'Baseline': BASE_DIR / "serial" / "serial_data_close.csv",
    'Far': BASE_DIR / "serial" / "serial_data_far.csv",
    'Obstacle': BASE_DIR / "serial" / "serial_data_obstacle.csv",
    "Moving": BASE_DIR / "serial" / "serial_data_moving.csv"
}

OUTPUT_IMAGE_NAME = "Figure5.png"

# 2. 定義 CSI 數據解析函數 (自動提取 IQ 訊號並計算複數振幅)
def extract_average_csi_amplitude(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: Cannot find file at {file_path}")
        return None
    
    # 篩選出 type 為 'CSI' 的硬體原始資料
    csi_data_rows = df[df['type'] == 'CSI']['raw_line']
    
    all_amplitudes = []
    
    for row in csi_data_rows:
        if pd.isna(row):
            continue
        parts = row.split(',')
        if len(parts) < 7:
            continue
        
        # 第 7 個欄位 (parts[6]) 包含了以空格分隔的實部與虛部數值
        iq_string = parts[6].strip()
        iq_values = [int(val) for val in iq_string.split(' ') if val != '']
        
        # 奇數索引為實部 (Real)，偶數索引為虛部 (Imaginary)
        real_part = np.array(iq_values[0::2])
        imag_part = np.array(iq_values[1::2])
        
        # 確保長度對齊並計算振幅 (Amplitude = sqrt(R^2 + I^2))
        min_length = min(len(real_part), len(imag_part))
        if min_length == 0:
            continue
            
        amplitude = np.sqrt(real_part[:min_length]**2 + imag_part[:min_length]**2)
        all_amplitudes.append(amplitude)
        
    if not all_amplitudes:
        return None
        
    # 找出最普遍的子載波長度 (例如 ESP32 常見的 64 個有效子載波)
    standard_length = len(all_amplitudes[0])
    valid_amplitudes = [amp for amp in all_amplitudes if len(amp) == standard_length]
    
    # 計算時間軸上的平均振幅
    return np.mean(valid_amplitudes, axis=0)


# 3. 批次讀取並解析三份資料集
csi_profiles = {}
for label, path in files.items():
    print(f"Processing CSI data from {path.name}...")
    avg_amp = extract_average_csi_amplitude(path)
    if avg_amp is not None:
        csi_profiles[label] = avg_amp

# 4. 開始繪製 CSI 頻譜特徵對比圖
fig, ax = plt.subplots(figsize=(11, 6))

# 設定三種場景的顏色與線條樣式
styles = {
    'Baseline': {'color': '#1f77b4', 'linestyle': '-', 'linewidth': 2.0},
    'Far': {'color': '#2ca02c', 'linestyle': '-', 'linewidth': 2.0},
    'Moving': {'color': '#d62728', 'linestyle': '-', 'linewidth': 2.0},
    'Obstacle': {'color': '#ffcb0e', 'linestyle': '-', 'linewidth': 2.0}
}

# 繪製各場景的特徵曲線
for label, avg_amp in csi_profiles.items():
    subcarrier_index = np.arange(len(avg_amp))
    ax.plot(subcarrier_index, avg_amp, label=label, **styles[label])


# 5. 全英文圖表格式化設定 (全英文簡報、IEEE 論文等級外觀)
ax.set_title('CSI Subcarrier Amplitude Profile', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Subcarrier Index', fontsize=12, fontweight='bold')
ax.set_ylabel('Average CSI Amplitude', fontsize=12, fontweight='bold')
# ax.set_xlim(0, 55)  # 剔除前後不穩定的導頻(Pilot)區間，專注呈現核心有效子載波波形
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='upper right', fontsize=11, framealpha=0.95)

# 6. 優化排版並儲存
plt.tight_layout()
plt.savefig(OUTPUT_IMAGE_NAME, dpi=300)
print(f"🎉 Successfully analyzed and saved CSI comparison chart as '{OUTPUT_IMAGE_NAME}'!")