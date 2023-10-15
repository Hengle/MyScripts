import re
import subprocess
from collections import namedtuple
from typing import List

from _script import get_variable, set_variable
from _shutil import getch, print2

DeviceInfo = namedtuple("DeviceInfo", ["serial", "product", "battery_level", "key"])


def get_device_list() -> List[DeviceInfo]:
    current_serial = get_variable("ANDROID_SERIAL")
    print("ANDROID_SERIAL=%s" % current_serial)
    print()

    lines = subprocess.check_output(["adb", "devices"], universal_newlines=True).split(
        "\n"
    )
    lines = lines[1:]
    device_list = []
    used_key = set()
    for line in lines:
        if line.strip():
            serial, _ = line.split()

            # Get product name
            try:
                product = subprocess.check_output(
                    ["adb", "-s", serial, "shell", "getprop", "ro.build.product"],
                    universal_newlines=True,
                ).strip()

                # Get battery level
                out = subprocess.check_output(
                    ["adb", "-s", serial, "shell", "dumpsys", "battery"],
                    universal_newlines=True,
                )
                match = re.findall("level: (\d+)", out)
                if match:
                    battery_level = match[0]
                else:
                    battery_level = None
            except subprocess.CalledProcessError:
                continue

            # Find next unused key
            for key in product:
                key = key.lower()
                if key not in used_key:
                    used_key.add(key)
                    break

            print(
                "[%s] %s"
                % (
                    key,
                    serial,
                ),
                end="",
            )
            print2(" %s" % product, color="green", end="")
            print(" Battery=%s" % battery_level, end="")
            if current_serial == serial:
                print2(" (*)", color="red", end="")
            device_list.append(DeviceInfo(serial, product, battery_level, key))
            print()

    print("[0] Clear ANDROID_SERIAL")
    print()
    return device_list


def select_default_android_device():
    while True:
        device_list = get_device_list()
        ch = getch()
        for device in device_list:
            if ch == device.key:
                set_variable("ANDROID_SERIAL", device.serial)
                return
            elif ch == "0":
                set_variable("ANDROID_SERIAL", "")
                return


if __name__ == "__main__":
    while True:
        select_default_android_device()