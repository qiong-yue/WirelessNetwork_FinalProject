import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re

# 1. 基礎設定與檔案路徑
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_IMAGE_NAME = "Figure8.png"

# 2. 定義資料載入與 RSSI 提取函數
def load_and_process(file_name):
    target_path = BASE_DIR / "network" / file_name
    try:
        df = pd.read_csv(target_path)
    except FileNotFoundError:
        print(f"Error: Cannot find file at {target_path}")
        return None
        
    def extract_rssi(text):
        if pd.isna(text): return None
        match = re.search(r'RSSI=(-?\d+)', str(text))
        return int(match.group(1)) if match else None
        
    df['rssi'] = df['ack_msg'].apply(extract_rssi)
    return df

df_close = load_and_process('network_perf_close.csv')
df_csma = load_and_process('network_perf_CSMA.csv')

# 3. 計算右圖所需的統計指標 (丟包率與延遲)
def calculate_stats(df):
    total = len(df)
    timeouts = len(df[df['status'] == 'TIMEOUT'])
    loss_rate = (timeouts / total) * 100
    avg_rtt = df['rtt_ms'].mean()
    return loss_rate, avg_rtt

loss_close, rtt_close = calculate_stats(df_close)
loss_csma, rtt_csma = calculate_stats(df_csma)

# 4. 開始建立 1列2行 的高對比畫布
fig, (ax1, ax3) = plt.subplots(1, 2, figsize=(16, 6.5))

# ==========================================
# 左圖：RTT 與 RSSI 實時時序對比 (雙 Y 軸)
# ==========================================
# 軸線 A (左 Y 軸)：繪製兩者的 RTT 延遲
line_close_rtt = ax1.plot(df_close['seq'], df_close['rtt_ms'], color='#2ca02c', marker='o', 
                          linestyle='-', alpha=0.5, label='Baseline: RTT (ms)')
line_csma_rtt = ax1.plot(df_csma['seq'], df_csma['rtt_ms'], color="#55ff55", marker='^', 
                         linestyle='-', linewidth=2, label='Contention: RTT (ms)')

# 標記 CSMA 的 TIMEOUT (超時丟包)
csma_timeouts = df_csma[df_csma['status'] == 'TIMEOUT']
if not csma_timeouts.empty:
    max_val = max(df_csma['rtt_ms'].max(), df_close['rtt_ms'].max())
    ax1.scatter(csma_timeouts['seq'], [max_val * 1.05] * len(csma_timeouts), 
                color='#d62728', marker='x', s=70, linewidths=2, label='Contention: TIMEOUT')

ax1.set_title('RTT & RSSI Contrast (Baseline vs. Contention)', fontsize=13, fontweight='bold', pad=15)
ax1.set_xlabel('Packet Sequence Number (seq)', fontsize=11, fontweight='bold')
ax1.set_ylabel('RTT Latency (ms)', color='#2ca02c', fontsize=11, fontweight='bold')
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.set_ylim(0, max(df_csma['rtt_ms'].max(), df_close['rtt_ms'].max()) * 1.2)

# 軸線 B (右 Y 軸)：共享 X 軸，繪製兩者的 RSSI
ax2 = ax1.twinx()
line_close_rssi = ax2.plot(df_close['seq'], df_close['rssi'], color='#1f77b4', marker='o', 
                           linestyle=':', alpha=0.5, label='Baseline: RSSI (dBm)')
line_csma_rssi = ax2.plot(df_csma['seq'], df_csma['rssi'], color="#32aaff", marker='s', 
                          linestyle='--', linewidth=1.5, label='Contention: RSSI (dBm)')

ax2.set_ylabel('RSSI (dBm)', color='#1f77b4',fontsize=11, fontweight='bold')
ax2.set_ylim(-100, -30)

# 合併左圖雙軸的圖例
lines_left = line_close_rtt + line_csma_rtt + line_close_rssi + line_csma_rssi
labels_left = [l.get_label() for l in lines_left]
ax1.legend(lines_left, labels_left, loc='upper right', fontsize=9, framealpha=0.9)

# ==========================================
# 右圖：Packet Loss Rate 與 Average RTT 對比長條圖
# ==========================================
categories = ['Baseline', 'CSMA Contention']
x_pos = np.arange(len(categories))
bar_width = 0.35

# 右圖左 Y 軸：Packet Loss Rate (紅色系長條)
rects_loss = ax3.bar(x_pos - bar_width/2, [loss_close, loss_close + loss_csma], bar_width, 
                     color='#2ca02c', edgecolor='#2ca02c', alpha=0.85, label='Packet Loss Rate (%)')
ax3.set_ylabel('Packet Loss Rate (%)', color='#2ca02c', fontsize=11, fontweight='bold')
ax3.tick_params(axis='y', labelcolor='#2ca02c')
ax3.set_xticks(x_pos)
ax3.set_xticklabels(categories, fontsize=11, fontweight='bold')
ax3.set_title('Statistical Summary: Packet Loss & Avg Latency', fontsize=13, fontweight='bold', pad=15)

# 右圖右 Y 軸：Average RTT (藍色系長條)
ax4 = ax3.twinx()
rects_rtt = ax4.bar(x_pos + bar_width/2, [rtt_close, rtt_csma], bar_width, 
                    color='#1f77b4', edgecolor='#1f77b4', alpha=0.85, label='Avg RTT Latency (ms)')
ax4.set_ylabel('Average RTT Latency (ms)', color='#1f77b4', fontsize=11, fontweight='bold')
ax4.tick_params(axis='y', labelcolor='#1f77b4')

# 限制右圖 Y 軸上限以防標籤重疊
ax3.set_ylim(0, max(loss_close, loss_csma) * 1.3)
ax4.set_ylim(0, max(rtt_close, rtt_csma) * 1.3)

# 為長條圖加上數值標籤
def label_bars(rects, ax, suffix=""):
    for rect in rects:
        h = rect.get_height()
        ax.annotate(f'{h:.1f}{suffix}',
                    xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

label_bars(rects_loss, ax3, "%")
label_bars(rects_rtt, ax4, " ms")

# 5. 全局調整並儲存
plt.tight_layout()
plt.savefig(OUTPUT_IMAGE_NAME, dpi=300)
print(f"🎉 成功生成直觀強烈對比的 Figure 8：'{OUTPUT_IMAGE_NAME}'")