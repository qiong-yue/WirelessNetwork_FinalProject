import os
import re
import csv
import math
import pandas as pd
import matplotlib.pyplot as plt


#**********資料夾設定**********#
DATA_DIR = "experiment_data"
OUTPUT_DIR = "analysis_result"

os.makedirs(OUTPUT_DIR, exist_ok=True)


#**********實驗檔案設定**********#
SCENARIOS = {
    "close": {
        "network": f"{DATA_DIR}/network_perf_close.csv",
        "serial": f"{DATA_DIR}/serial_data_close.csv"
    },
    "far": {
        "network": f"{DATA_DIR}/network_perf_far.csv",
        "serial": f"{DATA_DIR}/serial_data_far.csv"
    },
    "obstacle": {
        "network": f"{DATA_DIR}/network_perf_obstacle.csv",
        "serial": f"{DATA_DIR}/serial_data_obstacle.csv"
    },
    "moving": {
        "network": f"{DATA_DIR}/network_perf_moving.csv",
        "serial": f"{DATA_DIR}/serial_data_moving.csv"
    }
}


#**********讀取 Network CSV**********#
def load_network_data(file_path):
    df = pd.read_csv(file_path)

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["rtt_ms"] = pd.to_numeric(df["rtt_ms"], errors="coerce")
    df["status"] = df["status"].astype(str)

    df["success"] = df["status"].str.contains("SUCCESS", na=False)
    df["timeout"] = df["status"].str.contains("TIMEOUT", na=False)

    df_success = df[df["success"] & df["rtt_ms"].notna()].copy()

    return df, df_success


#**********讀取 Serial CSV 並擷取 RSSI**********#
def load_serial_rssi(file_path):
    rows = []

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            timestamp = pd.to_datetime(row["timestamp"], errors="coerce")
            raw_line = str(row["raw_line"]).strip()

            if raw_line.startswith("RSSI"):
                match = re.search(r"(-?\d+)\s*dBm", raw_line)

                if match:
                    rssi = int(match.group(1))
                    rows.append([timestamp, rssi])

            elif raw_line.startswith("RSSI_DATA"):
                parts = raw_line.split(",")

                if len(parts) >= 3:
                    try:
                        rssi = int(parts[2])
                        rows.append([timestamp, rssi])
                    except:
                        pass

    df = pd.DataFrame(rows, columns=["timestamp", "rssi"])

    if df.empty:
        return df

    df = df.dropna()
    df["timestamp_sec"] = df["timestamp"].dt.floor("s")

    # 同一秒多筆 RSSI 取平均，避免圖表跳動太亂
    df = df.groupby("timestamp_sec", as_index=False)["rssi"].mean()
    df = df.rename(columns={"timestamp_sec": "timestamp"})

    return df


#**********計算 Jitter**********#
def calculate_jitter(rtt_series):
    rtt = rtt_series.dropna().tolist()

    if len(rtt) < 2:
        return math.nan

    diff = []

    for i in range(1, len(rtt)):
        diff.append(abs(rtt[i] - rtt[i - 1]))

    return sum(diff) / len(diff)


#**********計算統計資料**********#
def calculate_summary(all_data):
    rows = []

    for scenario, data in all_data.items():
        network_all = data["network_all"]
        network_success = data["network_success"]
        rssi_df = data["rssi"]

        total_packets = len(network_all)
        success_packets = len(network_success)
        timeout_packets = int(network_all["timeout"].sum())

        success_rate = success_packets / total_packets * 100 if total_packets > 0 else 0
        packet_loss = 100 - success_rate

        avg_rtt = network_success["rtt_ms"].mean()
        min_rtt = network_success["rtt_ms"].min()
        max_rtt = network_success["rtt_ms"].max()
        jitter = calculate_jitter(network_success["rtt_ms"])

        avg_rssi = rssi_df["rssi"].mean() if not rssi_df.empty else math.nan
        min_rssi = rssi_df["rssi"].min() if not rssi_df.empty else math.nan
        max_rssi = rssi_df["rssi"].max() if not rssi_df.empty else math.nan

        rows.append({
            "scenario": scenario,
            "total_packets": total_packets,
            "success_packets": success_packets,
            "timeout_packets": timeout_packets,
            "success_rate_percent": round(success_rate, 2),
            "packet_loss_percent": round(packet_loss, 2),
            "avg_rtt_ms": round(avg_rtt, 2) if not math.isnan(avg_rtt) else "",
            "min_rtt_ms": round(min_rtt, 2) if not math.isnan(min_rtt) else "",
            "max_rtt_ms": round(max_rtt, 2) if not math.isnan(max_rtt) else "",
            "jitter_ms": round(jitter, 2) if not math.isnan(jitter) else "",
            "avg_rssi_dbm": round(avg_rssi, 2) if not math.isnan(avg_rssi) else "",
            "min_rssi_dbm": round(min_rssi, 2) if not math.isnan(min_rssi) else "",
            "max_rssi_dbm": round(max_rssi, 2) if not math.isnan(max_rssi) else ""
        })

    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(f"{OUTPUT_DIR}/summary.csv", index=False, encoding="utf-8-sig")

    return summary_df


#**********無資料圖提示**********#
def draw_no_data(title, ylabel, output_name, message):
    plt.figure(figsize=(8, 5))
    plt.title(title)
    plt.ylabel(ylabel)

    plt.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        fontsize=14,
        transform=plt.gca().transAxes
    )

    plt.xticks([])
    plt.yticks([])
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/{output_name}", dpi=300)
    plt.close()


#**********圖一：各場景 RTT Over Time**********#
def plot_rtt_over_time(all_data):
    for scenario, data in all_data.items():
        df = data["network_success"]

        if df.empty:
            draw_no_data(
                f"RTT Over Time - {scenario}",
                "RTT (ms)",
                f"rtt_over_time_{scenario}.png",
                "No valid RTT data"
            )
            continue

        plt.figure(figsize=(10, 5))

        plt.plot(
            df["timestamp"],
            df["rtt_ms"],
            marker="o",
            markersize=3,
            linewidth=1.2
        )

        plt.title(f"RTT Over Time - {scenario}")
        plt.xlabel("Time")
        plt.ylabel("RTT (ms)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/rtt_over_time_{scenario}.png", dpi=300)
        plt.close()


#**********圖二：各場景 RSSI Over Time**********#
def plot_rssi_over_time(all_data):
    for scenario, data in all_data.items():
        df = data["rssi"]

        if df.empty:
            draw_no_data(
                f"RSSI Over Time - {scenario}",
                "RSSI (dBm)",
                f"rssi_over_time_{scenario}.png",
                "No RSSI data"
            )
            continue

        plt.figure(figsize=(10, 5))

        plt.plot(
            df["timestamp"],
            df["rssi"],
            marker="o",
            markersize=3,
            linewidth=1.2
        )

        plt.title(f"RSSI Over Time - {scenario}")
        plt.xlabel("Time")
        plt.ylabel("RSSI (dBm)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/rssi_over_time_{scenario}.png", dpi=300)
        plt.close()


#**********圖三：各場景 RSSI vs RTT**********#
def plot_rssi_vs_rtt_each(all_data):
    for scenario, data in all_data.items():
        network_df = data["network_success"].copy()
        rssi_df = data["rssi"].copy()

        if network_df.empty or rssi_df.empty:
            draw_no_data(
                f"RSSI vs RTT - {scenario}",
                "RTT (ms)",
                f"rssi_vs_rtt_{scenario}.png",
                "No matched RSSI and RTT data"
            )
            continue

        network_df = network_df.sort_values("timestamp")
        rssi_df = rssi_df.sort_values("timestamp")

        merged_df = pd.merge_asof(
            network_df,
            rssi_df,
            on="timestamp",
            direction="nearest",
            tolerance=pd.Timedelta(seconds=2)
        )

        merged_df = merged_df.dropna(subset=["rtt_ms", "rssi"])

        if merged_df.empty:
            draw_no_data(
                f"RSSI vs RTT - {scenario}",
                "RTT (ms)",
                f"rssi_vs_rtt_{scenario}.png",
                "No matched RSSI and RTT data"
            )
            continue

        plt.figure(figsize=(8, 6))

        plt.scatter(
            merged_df["rssi"],
            merged_df["rtt_ms"],
            alpha=0.75,
            s=20
        )

        plt.title(f"RSSI vs RTT - {scenario}")
        plt.xlabel("RSSI (dBm)")
        plt.ylabel("RTT (ms)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/rssi_vs_rtt_{scenario}.png", dpi=300)
        plt.close()


#**********圖四：Average RTT Comparison**********#
def plot_avg_rtt(summary_df):
    df = summary_df.copy()
    df["avg_rtt_ms"] = pd.to_numeric(df["avg_rtt_ms"], errors="coerce")
    df = df.dropna(subset=["avg_rtt_ms"])

    if df.empty:
        draw_no_data(
            "Average RTT Comparison",
            "Average RTT (ms)",
            "average_rtt_comparison.png",
            "No valid RTT data"
        )
        return

    plt.figure(figsize=(8, 5))
    plt.bar(df["scenario"], df["avg_rtt_ms"])
    plt.title("Average RTT Comparison")
    plt.xlabel("Scenario")
    plt.ylabel("Average RTT (ms)")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/average_rtt_comparison.png", dpi=300)
    plt.close()


#**********圖五：Jitter Comparison**********#
def plot_jitter(summary_df):
    df = summary_df.copy()
    df["jitter_ms"] = pd.to_numeric(df["jitter_ms"], errors="coerce")
    df = df.dropna(subset=["jitter_ms"])

    if df.empty:
        draw_no_data(
            "Jitter Comparison",
            "Jitter (ms)",
            "jitter_comparison.png",
            "No valid jitter data"
        )
        return

    plt.figure(figsize=(8, 5))
    plt.bar(df["scenario"], df["jitter_ms"])
    plt.title("Jitter Comparison")
    plt.xlabel("Scenario")
    plt.ylabel("Jitter (ms)")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/jitter_comparison.png", dpi=300)
    plt.close()


#**********圖六：Packet Loss Comparison**********#
def plot_packet_loss(summary_df):
    plt.figure(figsize=(8, 5))
    plt.bar(summary_df["scenario"], summary_df["packet_loss_percent"])
    plt.title("Packet Loss Comparison")
    plt.xlabel("Scenario")
    plt.ylabel("Packet Loss (%)")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/packet_loss_comparison.png", dpi=300)
    plt.close()


#**********圖七：Average RSSI Comparison**********#
def plot_avg_rssi(summary_df):
    df = summary_df.copy()
    df["avg_rssi_dbm"] = pd.to_numeric(df["avg_rssi_dbm"], errors="coerce")
    df = df.dropna(subset=["avg_rssi_dbm"])

    if df.empty:
        draw_no_data(
            "Average RSSI Comparison",
            "Average RSSI (dBm)",
            "average_rssi_comparison.png",
            "No valid RSSI data"
        )
        return

    plt.figure(figsize=(8, 5))
    plt.bar(df["scenario"], df["avg_rssi_dbm"])
    plt.title("Average RSSI Comparison")
    plt.xlabel("Scenario")
    plt.ylabel("Average RSSI (dBm)")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/average_rssi_comparison.png", dpi=300)
    plt.close()


#**********主程式**********#
def main():
    all_data = {}

    for scenario, files in SCENARIOS.items():
        network_file = files["network"]
        serial_file = files["serial"]

        if not os.path.exists(network_file):
            print(f"[Warning] Missing network file: {network_file}")
            continue

        if not os.path.exists(serial_file):
            print(f"[Warning] Missing serial file: {serial_file}")
            continue

        print(f"[Load] Scenario: {scenario}")

        network_all, network_success = load_network_data(network_file)
        rssi_df = load_serial_rssi(serial_file)

        all_data[scenario] = {
            "network_all": network_all,
            "network_success": network_success,
            "rssi": rssi_df
        }

    if not all_data:
        print("[Error] No valid data found.")
        return

    summary_df = calculate_summary(all_data)

    plot_rtt_over_time(all_data)
    plot_rssi_over_time(all_data)
    plot_rssi_vs_rtt_each(all_data)

    plot_avg_rtt(summary_df)
    plot_jitter(summary_df)
    plot_packet_loss(summary_df)
    plot_avg_rssi(summary_df)

    print("[Done] Analysis completed.")
    print(f"[Done] Results saved in: {OUTPUT_DIR}/")
    print(summary_df)


if __name__ == "__main__":
    main()