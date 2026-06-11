import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# 設定繪圖風格
sns.set_theme(style="whitegrid")
plt.rcParams["font.sans-serif"] = ["Arial", "Microsoft JhengHei"]  # 支援英文與微軟正黑體
plt.rcParams["axes.unicode_minus"] = False


def parse_csi_line(line):
    """解析單行 CSI_DATA，提取 RSSI 與計算子載波振幅 (Amplitude)"""
    if "CSI_DATA" not in line:
        return None

    # 處理可能因序列埠接收不全導致的前端雜訊，定位到 CSI_DATA 開始處
    idx = line.find("CSI_DATA")
    line_clean = line[idx:]

    parts = line_clean.strip().split(",")
    if len(parts) < 7:
        return None

    try:
        rssi = int(parts[3])
        data_str = parts[6]
        subcarriers = [int(x) for x in data_str.split()]

        # 原始數據為[實部, 虛部, 實部, 虛部...] 交錯排列
        # 計算複數特徵的模長（振幅）： $\sqrt{\text{Real}^2 + \text{Imag}^2}$
        amplitudes = []
        for i in range(0, len(subcarriers), 2):
            if i + 1 < len(subcarriers):
                real = subcarriers[i]
                imag = subcarriers[i + 1]
                amp = np.sqrt(real**2 + imag**2)
                amplitudes.append(amp)

        return {"rssi": rssi, "amplitudes": amplitudes}
    except Exception:
        return None


# 1. 定義要讀取的檔案列表
files = [
    "serial_data_close.csv",
    "serial_data_CSMA.csv",
    "serial_data_far.csv",
    "serial_data_moving.csv",
    "serial_data_obstacle.csv",
]

data_summary = {}

# 2. 讀取並解析數據
print("開始解析 CSI 數據檔案...")
for f in files:
    if not os.path.exists(f):
        print(f"警告: 找不到檔案 {f}，跳過。")
        continue

    # 提取場景標籤 (例如 serial_data_close.csv -> close)
    label = f.replace("serial_data_", "").replace(".csv", "")

    df = pd.read_csv(f)
    rssis = []
    amps_matrix = []

    for line in df["raw_line"].dropna():
        res = parse_csi_line(line)
        # 確保解析成功且子載波數量符合預期的 64 個
        if res and len(res["amplitudes"]) == 64:
            rssis.append(res["rssi"])
            amps_matrix.append(res["amplitudes"])

    if amps_matrix:
        data_summary[label] = {"rssi": rssis, "amps": np.array(amps_matrix)}
        print(f"成功解析【{label}】: 共有 {len(rssis)} 筆有效 CSI 記錄")

# 定義圖表顏色，確保對比鮮明
colors = ["#1f77b4", "#ff770f", "#2ca02c", "#d62728", "#9467bd"]

# ==========================================
# 📊 圖一：RSSI 箱線圖比較
# ==========================================
print("\n正在生成圖一：RSSI 比較圖...")
plt.figure(figsize=(9, 5))
rssi_data = [data_summary[k]["rssi"] for k in data_summary]
labels = list(data_summary.keys())

plt.boxplot(
    rssi_data,
    labels=labels,
    patch_artist=True,
    boxprops=dict(facecolor="#d6e4f0", color="#1f77b4"),
    medianprops=dict(color="red", linewidth=2),
)

plt.title("RSSI Distribution Across Different Scenarios", fontsize=14, pad=15)
plt.ylabel("RSSI (dBm)", fontsize=12)
plt.xlabel("Scenarios", fontsize=12)
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig("rssi_comparison.png", dpi=300)
plt.close()

# ==========================================
# 📊 圖二：平均 CSI 振幅譜線圖
# ==========================================
print("正在生成圖二：CSI 平均振幅譜線圖...")
plt.figure(figsize=(11, 6))

for i, (label, d) in enumerate(data_summary.items()):
    mean_amp = np.mean(d["amps"], axis=0)
    avg_rssi = np.mean(d["rssi"])
    plt.plot(
        mean_amp,
        label=f"{label} (Avg RSSI: {avg_rssi:.1f} dBm)",
        color=colors[i],
        linewidth=2,
    )

plt.title("Average CSI Amplitude Spectrum Comparison", fontsize=14, pad=15)
plt.xlabel("Subcarrier Index", fontsize=12)
plt.ylabel("CSI Amplitude", fontsize=12)
plt.legend(fontsize=10, loc="upper right")
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig("csi_amplitude_spectrum.png", dpi=300)
plt.close()

# ==========================================
# 📊 圖三：CSI 振幅標準差圖（環境動態敏感度）
# ==========================================
print("正在生成圖三：CSI 標準差波動圖...")
plt.figure(figsize=(11, 6))

for i, (label, d) in enumerate(data_summary.items()):
    std_amp = np.std(d["amps"], axis=0)
    plt.plot(
        std_amp,
        label=f"{label} (Volatility)",
        color=colors[i],
        linewidth=2,
        linestyle="--",
    )

plt.title(
    "CSI Amplitude Standard Deviation (Subcarrier Volatility)",
    fontsize=14,
    pad=15,
)
plt.xlabel("Subcarrier Index", fontsize=12)
plt.ylabel("Standard Deviation", fontsize=12)
plt.legend(fontsize=10, loc="upper right")
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig("csi_amplitude_std.png", dpi=300)
plt.close()

print("\n所有圖表已成功生成並儲存至當前資料夾！")