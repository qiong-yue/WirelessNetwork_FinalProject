import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re

# 1. 基礎設定與檔案路徑 (保留您的路徑邏輯，此處以 obstacle 為例)
BASE_DIR = Path(__file__).resolve().parent
FILE_NAME = "network_perf_moving.csv" 
OUTPUT_FILENAME = "Figure11.png"

network_path = BASE_DIR / "network" / FILE_NAME

# 讀取數據集
df = pd.read_csv(network_path)

# ==========================================
# 新增：從 ack_msg 欄位中精準提取 RSSI 數值
# ==========================================
def extract_rssi(text):
    if pd.isna(text):
        return None
    # 搜尋 RSSI= 後面的正負整數
    match = re.search(r'RSSI=(-?\d+)', str(text))
    return int(match.group(1)) if match else None

df['rssi'] = df['ack_msg'].apply(extract_rssi)


# 2. 建立並排子圖 (1 列 2 行)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))

# ==========================================
# 左圖：RTT 延遲 與 RSSI 雙軸時序圖 (Timeline)
# ==========================================
# 軸線 A (左 Y 軸)：繪製 RTT 延遲
line_rtt = ax1.plot(df['seq'], df['rtt_ms'], marker='o', linestyle='-', 
                    color='#1f77b4', linewidth=1.5, markersize=5, label='RTT (ms)')

# 自動辨識 TIMEOUT 封包，並在圖表上方用紅色 'X' 標記出來
timeouts = df[df['status'] == 'TIMEOUT']
scat_timeout = None
if not timeouts.empty:
    max_rtt = df['rtt_ms'].max() if pd.notna(df['rtt_ms'].max()) else 100
    scat_timeout = ax1.scatter(timeouts['seq'], [max_rtt * 1.1] * len(timeouts), 
                               color='#d62728', marker='x', s=80, linewidths=2, label='TIMEOUT')

ax1.set_xlabel("Packet Sequence Number (seq)", fontsize=12)
ax1.set_ylabel("RTT Latency (ms)", fontsize=12, color='#1f77b4')
ax1.tick_params(axis='y', labelcolor='#1f77b4')
ax1.grid(True, linestyle='--', alpha=0.5)

# 軸線 B (右 Y 軸)：共享 X 軸，獨立右邊 Y 軸繪製 RSSI
ax1_rssi = ax1.twinx()
line_rssi = ax1_rssi.plot(df['seq'], df['rssi'], marker='s', linestyle='--', 
                          color='#2ca02c', linewidth=1.2, markersize=4, label='RSSI (dBm)')
ax1_rssi.set_ylabel("RSSI (dBm)", fontsize=12, color='#2ca02c')
ax1_rssi.tick_params(axis='y', labelcolor='#2ca02c')

# 整合左軸與右軸的圖例 (Legend) 到同一個框框中
lines = line_rtt + line_rssi
if scat_timeout is not None:
    lines.append(scat_timeout)
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper right', fontsize=10, framealpha=0.9)

ax1.set_title("RTT Latency & RSSI Timeline", fontsize=14, fontweight='bold', pad=10)


# ==========================================
# 右圖：RTT 延遲分佈直方圖 (Histogram) - 保留原本優秀設計
# ==========================================
rtt_clean = df['rtt_ms'].dropna()
n, bins, patches = ax2.hist(rtt_clean, bins=15, color='#a1c9f4', edgecolor='#1f77b4', alpha=0.8, rwidth=0.9)
ax2.set_title("RTT Latency Distribution", fontsize=14, fontweight='bold', pad=10)
ax2.set_xlabel("RTT Latency (ms)", fontsize=12)
ax2.set_ylabel("Frequency", fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.5)


# 4. 優化佈局，確保標籤與標題不會重疊或被裁切
plt.tight_layout()

# 5. 儲存圖片
plt.savefig(OUTPUT_FILENAME, dpi=300)
print(f"圖表已成功繪製並儲存為：{OUTPUT_FILENAME}")