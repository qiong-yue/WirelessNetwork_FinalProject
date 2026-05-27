import socket
import time

ESP32_IP = "192.168.1.121"  # 改成你的 ESP32 IP
UDP_PORT = 8888

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1)

for i in range(1, 11):
    msg = f"SEQ:{i}"
    print("send:", msg)

    sock.sendto(msg.encode(), (ESP32_IP, UDP_PORT))

    try:
        data, addr = sock.recvfrom(1024)
        print("recv:", data.decode())
    except socket.timeout:
        print("timeout")

    time.sleep(1)

sock.close()