import csv
import os
import socket
import serial
import threading
import time
from datetime import datetime


#**********基本設定**********#
SERIAL_PORT = "/dev/cu.usbmodem2101"
BAUD_RATE = 115200

ESP32_IP = "172.20.10.14"
ESP32_UDP_PORT = 8888

PING_INTERVAL_SEC = 1.0
UDP_TIMEOUT_SEC = 3.0


#**********實驗場景設定**********#
scenario_name = input("Enter scenario name，例如 close / far / obstacle / moving: ").strip()

if scenario_name == "":
    scenario_name = "test"


#**********輸出資料夾設定**********#
OUTPUT_DIR = "experiment_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

network_csv_name = os.path.join(OUTPUT_DIR, f"network_perf_{scenario_name}.csv")
serial_csv_name = os.path.join(OUTPUT_DIR, f"serial_data_{scenario_name}.csv")

print(f"[File] Network CSV: {network_csv_name}")
print(f"[File] Serial CSV : {serial_csv_name}")


#**********CSV 檔案設定**********#
network_file = open(network_csv_name, "w", newline="", encoding="utf-8")
network_writer = csv.writer(network_file)
network_writer.writerow(["seq", "timestamp", "rtt_ms", "status", "send_msg", "ack_msg"])

serial_file = open(serial_csv_name, "w", newline="", encoding="utf-8")
serial_writer = csv.writer(serial_file)
serial_writer.writerow(["timestamp", "type", "raw_line"])


#**********執行狀態設定**********#
running = True


#**********Serial 讀取執行緒**********#
def read_serial():
    global running

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"[Serial] Connected: {SERIAL_PORT}")
    except Exception as e:
        print(f"[Serial] Failed to open serial port: {e}")
        running = False
        return

    while running:
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if line:
                timestamp = datetime.now().isoformat(timespec="seconds")

                if line.startswith("RSSI_DATA"):
                    data_type = "RSSI"
                elif line.startswith("CSI_DATA"):
                    data_type = "CSI"
                else:
                    data_type = "RAW"

                serial_writer.writerow([timestamp, data_type, line])
                serial_file.flush()

                print(f"[Serial] {line}")

        except Exception as e:
            print(f"[Serial] Read error: {e}")

    ser.close()
    print("[Serial] Closed")


#**********UDP RTT 測試執行緒**********#
def measure_udp_rtt():
    global running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.bind(("0.0.0.0", 0))
    sock.settimeout(UDP_TIMEOUT_SEC)

    local_ip, local_port = sock.getsockname()

    print("[Network] UDP RTT test started")
    print(f"[Network] Local UDP port: {local_port}")
    print(f"[Network] Target ESP32: {ESP32_IP}:{ESP32_UDP_PORT}")

    seq = 0

    while running:
        seq += 1

        send_timestamp = time.time()
        message = f"PING,{seq},{send_timestamp}"

        start_time = time.perf_counter()

        try:
            print(f"[Network] send seq={seq}")

            sock.sendto(
                message.encode("utf-8"),
                (ESP32_IP, ESP32_UDP_PORT)
            )

            data, addr = sock.recvfrom(1024)

            end_time = time.perf_counter()
            rtt_ms = (end_time - start_time) * 1000

            ack_msg = data.decode("utf-8", errors="ignore").strip()
            status = "SUCCESS"

            print(f"[Network] recv from {addr}: {ack_msg}")
            print(f"[Network] seq={seq}, rtt={rtt_ms:.2f} ms")

        except socket.timeout:
            rtt_ms = ""
            ack_msg = ""
            status = "TIMEOUT"

            print(f"[Network] seq={seq}, timeout")

        except Exception as e:
            rtt_ms = ""
            ack_msg = ""
            status = f"ERROR: {e}"

            print(f"[Network] seq={seq}, error: {e}")

        timestamp = datetime.now().isoformat(timespec="seconds")

        network_writer.writerow([
            seq,
            timestamp,
            rtt_ms,
            status,
            message,
            ack_msg
        ])

        network_file.flush()

        time.sleep(PING_INTERVAL_SEC)

    sock.close()
    print("[Network] Closed")


#**********主程式**********#
def main():
    global running

    serial_thread = threading.Thread(target=read_serial)
    network_thread = threading.Thread(target=measure_udp_rtt)

    serial_thread.start()
    network_thread.start()

    try:
        while running:
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[Main] Stop requested")
        running = False

    serial_thread.join()
    network_thread.join()

    network_file.close()
    serial_file.close()

    print("[Main] All files saved")
    print("[Main] Program stopped")


if __name__ == "__main__":
    main()