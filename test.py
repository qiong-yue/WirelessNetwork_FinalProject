import stest

ser = stest.Serial("/dev/cu.usbmodem1101",115200)

while True:
    print(ser.readline().decode(errors="ignore"))