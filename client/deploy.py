import os
import glob
import time
import re

ports = glob.glob("/dev/tty.*")
for element in ports:
    print(element)
# port = input("Please input number of serial port: ")
# print('your selected: ', port)
PORT = "/dev/tty.SLAB_USBtoUART"
FIRMWARE = "esp32-idf3-20191222-v1.12-5-g42e45bd69.bin"

# this only for ESP32
os.system(f"esptool.py --chip esp32 --port {PORT} erase_flash")
print("read file list for upload")
# print(os.path.basename(__main__))
os.system(
    f"esptool.py --chip esp32 --port {PORT} --baud 460800 write_flash -z 0x1000 {FIRMWARE}"
)
time.sleep(10)

# Нужна задержка для перезагрузки модуля
# Создаем структуру каталогов
catalog = os.walk("lib")
for element in catalog:
    os.system(f"ampy -p {PORT} mkdir {element[0]}")
    print(f"directory '{element[0]}' is create")
print("Now reboot...")
os.system(f"ampy -p {PORT} reset")
time.sleep(10)


catalog = os.walk(".")
local_files = []
remote_files = []
for address, dirs, files in catalog:
    for element in files:
        if (
            not element[0] == "."
            and not element == "main.py"
            and not element == FIRMWARE
            and not element == "boot.py"
            and not re.search('./.git', address)
        ):
            local_files.append((address + "/" + element).split("./")[1])
            remote_files.append(address.split(".")[1] + "/" + element)
upload_files = zip(local_files, remote_files)
for element in upload_files:
    print(f"upload {element[0]}")
    os.system(f"ampy -p {PORT} put {element[0]} {element[1]}")
# os.system(f"ampy -p {PORT} put boot.py")
# os.system(f"ampy -p {PORT} put main.py")
os.system(f"ampy -p {PORT} reset")
