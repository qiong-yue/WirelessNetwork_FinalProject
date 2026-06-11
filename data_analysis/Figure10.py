import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re

# 1. 基礎設定與檔案路徑
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_IMAGE_NAME = "Figure10.png"

# 設定輸入檔案路徑 (對應您的專案目錄結構)
path_enabled = BASE_DIR / "network" / "network_perf_close.csv"
path_disabled = BASE_DIR / "network" / "network_perf_close_no_csi.csv"

# 2. 定義資料解析與指標計算函數
def load_and_process_metrics(target_path):
    try:
        df = pd.read_csv(target_path)
    except FileNotFoundError:
        print(f"Error: Cannot find file at {target_path}")
        return None
        
    # 利用正規表達式提取 RSSI 數值
    def extract_rssi(text):
        if pd.isna(text): return None
        match = re.search(r'RSSI=(-?\d+)', str(text))
        return int(match.group(1)) if match else None
        
    df['rssi'] = df['ack_msg'].apply(extract_rssi)
    return df

df_en = load_and_process_metrics(path_enabled)
df_dis = load_and_process_metrics(path_disabled)

if df_en is None or df_dis is None:
    print("Error loading CSV files. Please check paths.")
    exit()

# 計算右圖統計長條圖所需的數據 (丟包率、平均 RTT)
loss_en = (df_en['status'] == 'TIMEOUT').sum() / len(df_en) * 100
avg_rtt_en = df_en['rtt_ms'].mean()

loss_dis = (df_dis['status'] == 'TIMEOUT').sum() / len(df_dis) * 100
avg_rtt_dis = df_dis['rtt_ms'].mean()


# 3. 開始建立 1 列 2 行 的高效對比畫布 (遵守不使用 plt.figure() 規範)
fig, (ax1, ax3) = plt.subplots(1, 2, figsize=(16, 6.5))

# ==========================================
# 左圖：RTT 延遲 與 RSSI 實時時序對比 (雙 Y 軸折線圖)
# ==========================================
# 軸線 A (左 Y 軸)：繪製兩者的 RTT 延遲起伏
line_en_rtt = ax1.plot(df_en['seq'], df_en['rtt_ms'], color='#1f77b4', linestyle='-', 
                       linewidth=1.8, marker='o', markersize=4, label='Enabled: RTT (ms)')
line_dis_rtt = ax1.plot(df_dis['seq'], df_dis['rtt_ms'], color='#ff7f0e', linestyle='--', 
                        linewidth=1.5, marker='s', markersize=4, label='Disabled (No-CSI): RTT (ms)')

ax1.set_title('Real-time RTT & RSSI Timeline Contrast', fontsize=13, fontweight='bold', pad=15)
ax1.set_xlabel('Packet Sequence Number (seq)', fontsize=11, fontweight='bold')
ax1.set_ylabel('RTT Latency (ms)', fontsize=11, color='black', fontweight='bold')
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.set_ylim(0, max(df_en['rtt_ms'].max(), df_dis['rtt_ms'].max()) * 1.15)

# 軸線 B (右 Y 軸)：共享 X 軸，獨立右邊 Y 軸繪製兩者的 RSSI
ax2 = ax1.twinx()
line_en_rssi = ax2.plot(df_en['seq'], df_en['rssi'], color='#2ca02c', linestyle=':', 
                        linewidth=1.2, alpha=0.7, label='Enabled: RSSI (dBm)')
line_dis_rssi = ax2.plot(df_dis['seq'], df_dis['rssi'], color='#d62728', linestyle='-.', 
                         linewidth=1.2, alpha=0.7, label='Disabled (No-CSI): RSSI (dBm)')

ax2.set_ylabel('RSSI (dBm)', fontsize=11, color='black', fontweight='bold')
ax2.set_ylim(-100, -30)

# 整合左圖雙軸的 4 條線路圖例
all_lines = line_en_rtt + line_dis_rtt + line_en_rssi + line_dis_rssi
all_labels = [l.get_label() for l in all_lines]
ax1.legend(all_lines, all_labels, loc='upper right', fontsize=9, framealpha=0.9)


# ==========================================
# 右圖：Packet Loss Rate 與 Average RTT 對比 (雙 Y 軸長條圖)
# ==========================================
categories = ['CSI Enabled', 'CSI Disabled\n(No-CSI)']
x_pos = np.arange(len(categories))
bar_width = 0.35

# 右圖左 Y 軸：Packet Loss Rate (橘紅色系)
rects_loss = ax3.bar(x_pos - bar_width/2, [loss_en, loss_dis], bar_width, 
                     color='#ff9896', edgecolor='#d62728', alpha=0.85, label='Packet Loss Rate (%)')
ax3.set_ylabel('Packet Loss Rate (%)', color='#d62728', fontsize=11, fontweight='bold')
ax3.tick_params(axis='y', labelcolor='#d62728')
ax3.set_xticks(x_pos)
ax3.set_xticklabels(categories, fontsize=11, fontweight='bold')
ax3.set_title('Statistical Summary: Loss Rate & Avg Latency', fontsize=13, fontweight='bold', pad=15)

# 右圖右 Y 軸：Average RTT (藍灰色系)
ax4 = ax3.twinx()
rects_rtt = ax4.bar(x_pos + bar_width/2, [avg_rtt_en, avg_rtt_dis], bar_width, 
                    color='#aec7e8', edgecolor='#1f77b4', alpha=0.85, label='Avg RTT Latency (ms)')
ax4.set_ylabel('Average RTT Latency (ms)', color='#1f77b4', fontsize=11, fontweight='bold')
ax4.tick_params(axis='y', labelcolor='#1f77b4')

# 為長條圖上方自動標註精確數據
def label_bars(rects, ax, suffix=""):
    for rect in rects:
        h = rect.get_height()
        ax.annotate(f'{h:.1f}{suffix}',
                    xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

label_bars(rects_loss, ax3, "%")
label_bars(rects_rtt, ax4, " ms")

# 優化右圖上下邊界，防範標籤溢出
ax3.set_ylim(0, max(loss_en, loss_dis) * 1.3)
ax4.set_ylim(0, max(avg_rtt_en, avg_rtt_dis) * 1.3)


# 4. 全局細節優化與存檔
plt.tight_layout()
plt.savefig(OUTPUT_IMAGE_NAME, dpi=300)
print(f"🎉 成功生成全新 RTT/RSSI 時序與丟包/平均延遲綜合分析圖：'{OUTPUT_IMAGE_NAME}'")