import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re

# 1. 基礎設定與檔案路徑 
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_IMAGE_NAME = "Figure6.png"

# 定義要整合對比的三個核心資料集
data_files = {
    'close': 'network_perf_close.csv',
    'far': 'network_perf_far.csv',
    'moving': 'network_perf_moving.csv',
    'obstacle': 'network_perf_obstacle.csv'
}

# 2. 定義資料載入與 RSSI 自動提取函數
def load_and_extract_metrics(file_name):
    target_path = BASE_DIR / "network" / file_name
    try:
        df = pd.read_csv(target_path)
    except FileNotFoundError:
        print(f"Error: Cannot find file at {target_path}")
        return None
        
    # 利用正規表達式從 ack_msg 提取實時 RSSI
    def extract_rssi(text):
        if pd.isna(text):
            return None
        match = re.search(r'RSSI=(-?\d+)', str(text))
        return int(match.group(1)) if match else None
        
    df['rssi'] = df['ack_msg'].apply(extract_rssi)
    return df[['seq', 'rtt_ms', 'rssi', 'status']]

# 批次載入資料
data_scenarios = {}
for key, file_name in data_files.items():
    res = load_and_extract_metrics(file_name)
    if res is not None:
        data_scenarios[key] = res

# 3. 開始繪製 1列2行 的高對比度綜合圖表
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.5))

# 視覺風格設定 (定義三個情境的顏色與標記)
styles = {
    'close': {'label': 'Baseline', 'color': '#1f77b4', 'marker': 'o', 'alpha': 0.75, 'lw': 1.5},
    'far': {'label': 'Far Range', 'color': "#57c17c", 'marker': 's', 'alpha': 0.75, 'lw': 1.5},
    'obstacle': {'label': 'Obstacle', 'color': "#ffcb0e", 'marker': 'D', 'alpha': 0.75, 'lw': 1.5},
    'moving': {'label': 'Moving', 'color': '#d62728', 'marker': '^', 'alpha': 0.95, 'lw': 2.5, 'ms': 7}
}

# ==========================================
# 左圖：RSSI 實時強度對比 Timeline
# ==========================================
for key, df in data_scenarios.items():
    ax1.plot(df['seq'], df['rssi'], **styles[key])

ax1.set_title('RSSI Timeline Contrast', fontsize=13, fontweight='bold', pad=15)
ax1.set_xlabel('Packet Sequence Number (seq)', fontsize=11, fontweight='bold')
ax1.set_ylabel('RSSI (dBm)', fontsize=11, fontweight='bold')
ax1.set_ylim(-100, -30)  # 統一 Y 軸尺度，讓水位落差極度直觀
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='lower left', fontsize=10, framealpha=0.95)

# ==========================================
# 右圖：RTT 傳輸延遲對比 Timeline
# ==========================================
for key, df in data_scenarios.items():
    ax2.plot(df['seq'], df['rtt_ms'], **styles[key])

# # 特別針對 Moving 情境，將它後續引發的連續 TIMEOUT 在圖表上方標記出來，解釋為何線條中斷
# moving_df = data_scenarios.get('moving')
# if moving_df is not None:
#     moving_timeouts = moving_df[moving_df['status'] == 'TIMEOUT']
#     if not moving_timeouts.empty:
#         ax2.scatter(moving_timeouts['seq'], [520] * len(moving_timeouts), 
#                     color='#d62728', marker='x', s=65, linewidths=2, label='TIMEOUT')

ax2.set_title('RTT Latency Timeline', fontsize=13, fontweight='bold', pad=15)
ax2.set_xlabel('Packet Sequence Number (seq)', fontsize=11, fontweight='bold')
ax2.set_ylabel('RTT Latency (ms)', fontsize=11, fontweight='bold')
ax2.set_ylim(0, 580)  # 留出頂部天空給 TIMEOUT 標記
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='upper left', fontsize=10, framealpha=0.95)

# 4. 優化排版與存檔
plt.tight_layout()
plt.savefig(OUTPUT_IMAGE_NAME, dpi=300)
print(f"🎉 成功生成極具直觀對比性的全新 '{OUTPUT_IMAGE_NAME}'！")