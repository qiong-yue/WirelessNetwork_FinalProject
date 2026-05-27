import socket
import time

ESP32_IP = "192.168.1.121"  # 改成 ESP32 顯示的 IP
UDP_PORT = 8888

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)

for i in range(1, 6):
    msg = f"SEQ:{i}"
    print("SEND:", msg)

    sock.sendto(msg.encode(), (ESP32_IP, UDP_PORT))

    try:
        data, addr = sock.recvfrom(1024)
        print("RECV:", data.decode(errors="ignore"), "FROM", addr)
    except socket.timeout:
        print("TIMEOUT")

    time.sleep(5)

sock.close()