import utime as time
import network
import machine
import ulogging
import ujson as json

# TODO Вынести данную функцию
def load_config(config_file):
    try:
        with open(config_file) as f:
            config = json.load(f)
            f.close()
        return config
    except:
        # OSError: [Errno 2] ENOENT
        print("No such config file:", config_file)
        time.sleep(5)
        machine.reset()


def activate():
    config = load_config("config.json")
    try:
        wifi_if = network.WLAN(network.STA_IF)
        if not wifi_if.isconnected():
            print("connecting to network...")
        wifi_if.active(True)
        wifi_if.connect(config["ESSID"], config["PASSWORD"])
        #  Try connect to Access Point
        a = 0
        while not wifi_if.isconnected() and a != 5:
            print(".", end="")
            time.sleep(5)
            a += 1
            # If module cannot connect to WiFi - he's creates personal AP
        if not wifi_if.isconnected():
            wifi_if.disconnect()
            wifi_if.active(False)
            wifi_if = network.WLAN(network.AP_IF)
            wifi_if.active(True)
            wifi_if.config(
                essid=(config["AP-ESSID"]),
                authmode=network.AUTH_WPA_WPA2_PSK,
                password=(config["AP-PASSWORD"]),
                channel=int(config["CHANNEL"])
            )
            wifi_if.ifconfig(
                ("10.27.10.1", "255.255.255.0", "10.27.10.1", "10.27.10.1")
            )
        print("network config:", wifi_if.ifconfig())
    except RuntimeError:
        ulogging.info("Cannot init wifi")
        time.sleep(5)
        machine.reset()


def check_wifi_status():
    pass
    # TODO:
    # WLAN.status([param])
    # Return the current status of the wireless connection.
    # When called with no argument the return value describes the network link status.
    # The possible statuses are defined as constants:
    # STAT_IDLE – no connection and no activity,
    # STAT_CONNECTING – connecting in progress,
    # STAT_WRONG_PASSWORD – failed due to incorrect password,
    # STAT_NO_AP_FOUND – failed because no access point replied,
    # STAT_CONNECT_FAIL – failed due to other problems,
    # STAT_GOT_IP – connection successful.

