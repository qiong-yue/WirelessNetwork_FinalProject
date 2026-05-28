import serial

SERIAL_PORT = "/dev/cu.usbmodem2101"
BAUD_RATE = 115200

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

while True:
    line = ser.readline().decode(errors="ignore").strip()

    if line:
        print(line)