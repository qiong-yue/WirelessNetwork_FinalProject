import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re
import numpy as np

# 1. 基礎設定與檔案路徑 
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_IMAGE_NAME = "Figure4_2.png" 

# 3. 批次處理三份 CSV 資料集
files = {
    'Baseline': 'network_perf_close.csv',
    'Far': 'network_perf_far.csv',
    'Obstacle': 'network_perf_obstacle.csv',
    'Moving': 'network_perf_CSMA.csv'
}

scenarios = []
avg_rtts = []
loss_rates = []
avg_rssis = []


# 2. 定義資料解析函數：同時計算 RTT, 丟包率與自動提取 RSSI
def process_network_data(target_path):
    try:
        df = pd.read_csv(target_path)
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {target_path}")
        return None
  
    total_packets = len(df)
    timeout_packets = len(df[df['status'] == 'TIMEOUT'])
    
    # 計算封包丟失率 (Packet Loss Rate)
    loss_rate = (timeout_packets / total_packets) * 100
    
    # 計算平均 RTT 延遲 (剔除 TIMEOUT 的 NaN 值)
    avg_rtt = df['rtt_ms'].mean()
    
    # 利用正規表達式從 ack_msg (如 "ACK,PING,2,...,RSSI=-44") 提取 RSSI 數值
    def extract_rssi(text):
        if pd.isna(text):
            return None
        match = re.search(r'RSSI=(-?\d+)', str(text))
        return int(match.group(1)) if match else None
    
    df['rssi'] = df['ack_msg'].apply(extract_rssi)
    avg_rssi = df['rssi'].mean()
    
    return {
        'avg_rtt': avg_rtt,
        'loss_rate': loss_rate,
        'avg_rssi': avg_rssi
    }

# --- 修正後的迴圈部分：在這裡動態拼接路徑 ---
for label, file_name in files.items():
    # 正確將路徑拼接到 network 資料夾下
    full_network_path = BASE_DIR / "network" / file_name
    
    metrics = process_network_data(full_network_path)
    if metrics:
        scenarios.append(label)
        avg_rtts.append(metrics['avg_rtt'])
        loss_rates.append(metrics['loss_rate'])
        avg_rssis.append(metrics['avg_rssi'])

# 4. 開始繪製雙 Y 軸群組長條圖
x = np.arange(len(scenarios))
width = 0.35  # 長條圖寬度

# 初始化畫布 (遵守不使用 plt.figure() 規範)
fig, ax1 = plt.subplots(figsize=(10, 6))

# 左 Y 軸：平均 RTT 延遲 (藍色長條)
rects1 = ax1.bar(x - width/2, avg_rtts, width, label='Average RTT Latency (ms)', color='#1f77b4', alpha=0.85)
ax1.set_xlabel('Scenario', fontsize=12, labelpad=10)
ax1.set_ylabel('RTT Latency (ms)', color='#1f77b4', fontsize=12, fontweight='bold')
ax1.tick_params(axis='y', labelcolor='#1f77b4')
ax1.set_xticks(x)
ax1.set_xticklabels(scenarios, fontsize=11, fontweight='bold')
ax1.grid(True, linestyle='--', alpha=0.3)

# 右 Y 軸：封包丟失率 (粉紅/洋紅色長條)
ax2 = ax1.twinx()
rects2 = ax2.bar(x + width/2, loss_rates, width, label='Packet Loss Rate (%)', color='#2ca02c', alpha=0.85)
ax2.set_ylabel('Packet Loss Rate (%)', color='#2ca02c', fontsize=12, fontweight='bold')
ax2.tick_params(axis='y', labelcolor='#2ca02c')

# ==========================================
# 🌟 關鍵修正點 1：手動拉高雙軸的 Y 上限，為頂部留出 30% 的乾淨天空
# ==========================================
ax1.set_ylim(0, max(avg_rtts) * 1.35)
ax2.set_ylim(0, max(loss_rates) * 1.35 if max(loss_rates) > 0 else 100)

# 5. 在長條圖上方自動加上數值標籤
def add_labels(rects, ax, is_percent=False):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}{"%" if is_percent else " ms"}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 4),  # 向上偏移 4 個點
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

add_labels(rects1, ax1, is_percent=False)
add_labels(rects2, ax2, is_percent=True)

# ==========================================
# 🌟 關鍵修正點 2：將 RSSI 泡泡改由 ax2 繪製，並定位在最頂部的天空中
# ==========================================
# 使用 ax2.text 並設定 zorder=10，確保它永遠漂浮在粉紅色圖層的上方
for i, rssi in enumerate(avg_rssis):
    # 計算頂部懸浮的完美 Y 軸高度 (以右軸的最大數值再往上 12% 為基準)
    top_y_position = max(loss_rates) * 1.15 if max(loss_rates) > 0 else 85
    
    ax2.text(i, top_y_position, f"Average RSSI\n{rssi:.1f} dBm", 
             ha='center', va='center', color='black', weight='bold', fontsize=10, zorder=10,
             bbox=dict(boxstyle='round,pad=0.5', fc='#ffcc00', ec='#e6b800', alpha=0.9, zorder=10))

# 7. 加上圖表標題並優化排版
plt.title('Comparison', fontsize=15, fontweight='bold', pad=20)
plt.tight_layout()

# 8. 儲存圖片 (遵守規範不使用 plt.show())
plt.savefig(OUTPUT_IMAGE_NAME, dpi=300)
print(f"分析完成！圖表已成功存檔為 '{OUTPUT_IMAGE_NAME}'")