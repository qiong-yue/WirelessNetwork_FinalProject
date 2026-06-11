import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re

# 1. 基礎設定與檔案路徑 
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_IMAGE_NAME = "Figure9.png"

# 設定輸入檔案路徑 (若您的檔案在 network 資料夾下，請將 "." 改為 "network")
path_enabled = BASE_DIR / "network" / "network_perf_close.csv"
path_disabled = BASE_DIR / "network" / "network_perf_close_no_csi.csv"

# 2. 定義資料解析與網路指標計算函數
def calculate_network_metrics(target_path):
    try:
        df = pd.read_csv(target_path)
    except FileNotFoundError:
        print(f"Error: Cannot find file at {target_path}")
        return None
        
    # 提取有效的 RTT 陣列
    rtt_values = df['rtt_ms'].dropna().values
    
    # 計算延遲抖動 (Jitter): 鄰近封包延遲差值的絕對平均值值
    jitter_values = np.abs(np.diff(rtt_values))
    avg_jitter = np.mean(jitter_values) if len(jitter_values) > 0 else 0
    
    # 計算封包丟失率 (Packet Loss Rate)
    total_packets = len(df)
    timeout_packets = (df['status'] == 'TIMEOUT').sum()
    loss_rate = (timeout_packets / total_packets) * 100
    
    # 計算延遲中位數 (Median RTT)
    median_rtt = np.median(rtt_values)
    
    return rtt_values, avg_jitter, loss_rate, median_rtt

# 載入並計算兩組資料
metrics_en = calculate_network_metrics(path_enabled)
metrics_dis = calculate_network_metrics(path_disabled)

if metrics_en and metrics_dis:
    rtt_en, jit_en, loss_en, med_en = metrics_en
    rtt_dis, jit_dis, loss_dis, med_dis = metrics_dis
else:
    print("Error processing data files. Please check paths.")
    exit()

# 3. 建立 1 列 2 行 的高對比度子圖 (遵守不使用 plt.figure() 規範)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))

# ==========================================
# 左圖：RTT 延遲之累積強度分佈圖 (CDF Contrast)
# ==========================================
# 排序數據以計算 CDF
x_en = np.sort(rtt_en)
y_en = np.arange(1, len(x_en) + 1) / len(x_en)
x_dis = np.sort(rtt_dis)
y_dis = np.arange(1, len(x_dis) + 1) / len(x_dis)

ax1.plot(x_en, y_en, label='CSI Enabled', color='#1f77b4', linewidth=2.5)
ax1.plot(x_dis, y_dis, label='CSI Disabled', color='#ff7f0e', linewidth=2.5, linestyle='--')

ax1.set_title('Cumulative Distribution Function (CDF) of RTT Latency', fontsize=13, fontweight='bold', pad=12)
ax1.set_xlabel('RTT Latency (ms)', fontsize=11, fontweight='bold')
ax1.set_ylabel('Cumulative Probability', fontsize=11, fontweight='bold')
ax1.set_xlim(0, 400)
ax1.set_ylim(0, 1.05)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='lower right', fontsize=10)

# 在左圖標註兩者的中位數對齊線與焦點
ax1.axhline(0.5, color='gray', linestyle=':', alpha=0.5)
ax1.scatter([med_en, med_dis], [0.5, 0.5], color='#d62728', s=40, zorder=5)
ax1.annotate(f'Enabled Median: {med_en:.1f} ms', xy=(med_en, 0.5), xytext=(med_en + 25, 0.42),
             arrowprops=dict(arrowstyle="->", color='#1f77b4', lw=1), color='#1f77b4', weight='bold', fontsize=9.5)
ax1.annotate(f'Disabled Median: {med_dis:.1f} ms', xy=(med_dis, 0.5), xytext=(med_dis - 135, 0.55),
             arrowprops=dict(arrowstyle="->", color='#ff7f0e', lw=1), color='#ff7f0e', weight='bold', fontsize=9.5)


# ==========================================
# 右圖：Jitter 與 Packet Loss Rate 橫向對比 (Bar Chart Contrast)
# ==========================================
categories = ['Average Jitter (ms)', 'Packet Loss Rate (%)']
x_positions = np.arange(len(categories))
bar_width = 0.35

rects1 = ax2.bar(x_positions - bar_width/2, [jit_en, loss_en], bar_width, 
                 label='CSI Enabled', color='#1f77b4', alpha=0.85, edgecolor='#1f77b4')
rects2 = ax2.bar(x_positions + bar_width/2, [jit_dis, loss_dis], bar_width, 
                 label='CSI Disabled', color='#ff7f0e', alpha=0.85, edgecolor='#ff7f0e')

ax2.set_title('System Performance Metrics Analysis', fontsize=13, fontweight='bold', pad=12)
ax2.set_xticks(x_positions)
ax2.set_xticklabels(categories, fontsize=11, fontweight='bold')
ax2.set_ylabel('Metric Values', fontsize=11, fontweight='bold')
ax2.grid(True, linestyle=':', alpha=0.4)
ax2.legend(loc='upper right', fontsize=10)

# 為長條圖上方添加數值標籤
def add_bar_labels(rects):
    for rect in rects:
        height = rect.get_height()
        ax2.annotate(f'{height:.1f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 4), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

add_bar_labels(rects1)
add_bar_labels(rects2)

# 動態調整右圖 Y 軸上限，留出頂部空間防標籤重疊
ax2.set_ylim(0, max(jit_dis, loss_dis) * 1.25)


# 4. 全局調整排版並存檔
plt.tight_layout()
plt.savefig(OUTPUT_IMAGE_NAME, dpi=300)
print(f"🎉 成功生成包含 CDF、Jitter 與丟包率橫向對比的終極開銷分析圖：'{OUTPUT_IMAGE_NAME}'")