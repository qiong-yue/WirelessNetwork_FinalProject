import socket
import time
import stest
import threading
import csv

#**********基本設定**********#
ESP32_IP = "192.168.0.180"       # 改成 ESP32 印出的 IP
UDP_PORT = 8888

SERIAL_PORT = "/dev/cu.usbmodem1101"  # Mac 範例；Windows 改成 COM3
BAUD_RATE = 115200

TOTAL_PACKETS = 500
INTERVAL = 0.1  # 每 0.1 秒送一次 UDP

#**********CSV 檔案設定**********#
network_file = open("network_perf.csv", "w", newline="", encoding="utf-8")
network_writer = csv.writer(network_file)
network_writer.writerow(["seq", "rtt_ms", "status"])

serial_file = open("serial_data.csv", "w", newline="", encoding="utf-8")
serial_writer = csv.writer(serial_file)
serial_writer.writerow(["timestamp", "type", "raw_line"])

running = True


#**********Serial 讀取執行緒**********#
def read_serial():
    global running

    try:
        ser = stest.Serial(SERIAL_PORT, BAUD_RATE, timeout=10)
        print(f"[Serial] Connected: {SERIAL_PORT}")
    except Exception as e:
        print(f"[Serial] Failed to open serial port: {e}")
        return

    while running:
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if line:
                timestamp = time.time()

                if line.startswith("CSI_DATA"):
                    data_type = "CSI"
                elif line.startswith("STATUS"):
                    data_type = "STATUS"
                elif line.startswith("UDP_RX"):
                    data_type = "UDP_RX"
                else:
                    data_type = "OTHER"

                serial_writer.writerow([timestamp, data_type, line])
                print(f"[Serial] {line}")

        except Exception:
            pass

    ser.close()


#**********UDP RTT 測試**********#
def udp_test():
    global running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)

    print("[UDP] Start testing...")

    for seq in range(1, TOTAL_PACKETS + 1):
        message = f"SEQ:{seq}"
        send_time = time.time()

        try:
            sock.sendto(message.encode(), (ESP32_IP, UDP_PORT))

            data, addr = sock.recvfrom(1024)
            receive_time = time.time()

            response = data.decode(errors="ignore")
            rtt_ms = (receive_time - send_time) * 1000

            network_writer.writerow([seq, round(rtt_ms, 2), "SUCCESS"])
            print(f"[UDP] {message} | RTT = {rtt_ms:.2f} ms | Response = {response}")

        except socket.timeout:
            network_writer.writerow([seq, -1, "LOST"])
            print(f"[UDP] {message} | LOST")

        time.sleep(INTERVAL)

    sock.close()
    running = False


#**********主程式**********#
if __name__ == "__main__":
    serial_thread = threading.Thread(target=read_serial)
    serial_thread.start()

    time.sleep(2)

    udp_test()

    serial_thread.join()

    network_file.close()
    serial_file.close()

    print("Done.")
    print("Saved: network_perf.csv")
    print("Saved: serial_data.csv")