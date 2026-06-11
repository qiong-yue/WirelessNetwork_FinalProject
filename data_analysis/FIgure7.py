import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 1. 基礎設定與檔案路徑
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_IMAGE_NAME = "Figure7.png"

# 設定三份原始 Serial CSI 資料路徑
files = {
    'Baseline': BASE_DIR / "serial" / "serial_data_close.csv",
    'Far': BASE_DIR / "serial" / "serial_data_far.csv",
    'Moving': BASE_DIR / "serial" / "serial_data_moving.csv"
}

# 2. 定義 CSI 二維矩陣提取函數 (對齊時間軸長度，以便直觀對比)
def extract_csi_heatmap_matrix(file_path, num_packets=15):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: Cannot find file at {file_path}")
        return None
        
    csi_rows = df[df['type'] == 'CSI']['raw_line'].dropna()
    matrix = []
    
    for row in csi_rows:
        parts = row.split(',')
        if len(parts) < 7:
            continue
        # 提取以空格分隔的 IQ 原始碼字串
        iq_str = parts[6].strip()
        iq_vals = [int(x) for x in iq_str.split(' ') if x != '']
        
        # 拆分實部與虛部並計算複數振幅
        real = np.array(iq_vals[0::2])
        imag = np.array(iq_vals[1::2])
        min_len = min(len(real), len(imag))
        if min_len == 0:
            continue
            
        amplitude = np.sqrt(real[:min_len]**2 + imag[:min_len]**2)
        matrix.append(amplitude)
        
    if not matrix:
        return None
        
    # 確保子載波長度一致，並截取相同的時間步長（封包數）進行公平對比
    target_subcarrier_len = len(matrix[0])
    matrix = [m for m in matrix if len(m) == target_subcarrier_len]
    matrix = np.array(matrix)
    
    if len(matrix) > num_packets:
        matrix = matrix[:num_packets]
        
    # 僅保留前 55 個核心有效子載波，剔除邊緣的高頻雜訊保護頻帶
    return matrix[:, :55]

# 3. 批次處理並載入三個場景的 CSI 二維矩陣
matrices = {}
for label, path in files.items():
    mat = extract_csi_heatmap_matrix(path, num_packets=15)
    if mat is not None:
        matrices[label] = mat

# 4. 開始繪製 1列3行 的並排 CSI 熱圖對比畫布 (遵守不使用 plt.figure() 規範)
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5.5))
axes = [ax1, ax2, ax3]

# 為了讓三個場景的能量對比具有絕對客觀性，我們統一使用相同的顏色標尺 (vmin, vmax)
# 根據資料集特性，將振幅上限設定為 22 以獲得最佳視覺對比度
v_min, v_max = 0, 22
cmap_style = 'viridis'  # 採用學術界最標準的 viridis 翠綠/黃藍色調

# 繪製各場景子圖
for idx, (label, mat) in enumerate(matrices.items()):
    ax = axes[idx]
    # imshow 二維展開：X 軸為子載波，Y 軸為封包序號（時間）
    im = ax.imshow(mat, aspect='auto', cmap=cmap_style, vmin=v_min, vmax=v_max, interpolation='none')
    
    # 格式化子圖設定 (全英文)
    ax.set_title(label, fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel("Subcarrier Index", fontsize=11, fontweight='bold')
    if idx == 0:
        ax.set_ylabel("Packet Index (Time Evolution)", fontsize=11, fontweight='bold')
    
    # 每個子圖右側配置獨立的能量對比 Colorbar
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('CSI Amplitude Strength', fontsize=10)

# 5. 全局標題與版面優化
plt.suptitle('CSI Spatial-Temporal Contrast', 
             fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()

# 6. 儲存圖片 (遵守規範不使用 plt.show())
plt.savefig(OUTPUT_IMAGE_NAME, dpi=300, bbox_inches='tight')
print(f"🎉 成功生成極具震撼對比度的全新 CSI 三矩陣熱圖：'{OUTPUT_IMAGE_NAME}'")