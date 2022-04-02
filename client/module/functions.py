import errno
import gc
import sys
import machine
import NFC_PN532 as nfc
import uasyncio as asyncio
import ubinascii
import ujson as json
import urequests as requests
import utime as time
from machine import SoftSPI, Pin


def free(full=False):
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F+A
    P = '{0:.2f}%'.format(F/T*100)
    if not full:
        return P
    else:
        return ('Total:{0} Free:{1} ({2})'.format(T,F,P))


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


def save_config(config, config_file):
    try:
        with open(config_file, "w") as f:
            json.dump(config, f)
            f.close()
    except:
        print("No such config file:", config_file) 


async def feed_watchdog(wdt):
    while True:
        wdt.feed()
        await asyncio.sleep(1)


# def load_data(data_file):
#     #try:
#     with open(data_file) as d:
#         data = json.load(d)
#         d.close()
#     return data
#     #except:
#      #   logging.info("No such data file:", data_file)
# 
# 
# def save_data(data, data_file):
#     try:
#         with open(data_file, "w") as d:
#             json.dump(data, d)
#             d.close()
#     except:
#         logging.info("No such data file:", data_file)
# 
# 
# def set_limit_handler(qs):
#     pass
#     # data_f = load_data("data.json")
#     # result1 = qs.replace("_", "=")
#     # result2 = result1.replace("&", "=")
#     # result3 = result2.split("=")
#     # day_limit_value = result3[2]
#     # number = result3[3]
#     # card = result3[4]
#     # value = result3[5]
#     # data_f[number][card] = int(value)
#     # data_f[number]["day limit"] = int(day_limit_value)
#     # save_data(data_f, "data.json")


def set_config_handler(qs):
    config = load_config("config.json")
    param = qs.split('&')
    for item in param:
        key, value = item.split('=')
        config[key] = value
    if not 'SYSLOG=True' in qs:
        config['SYSLOG'] = "False"
    save_config(config, 'config.json')


def init_card_reader():
    # PN532 module connect and initialize
    try:
        spi_dev = SoftSPI(baudrate=1000000, sck=Pin(5), mosi=Pin(23), miso=Pin(19))
        cs = Pin(22, Pin.OUT)
        cs.on()
        pn532 = nfc.PN532(spi_dev, cs)
        ic, ver, rev, support = pn532.get_firmware_version()
        print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))
        pn532.SAM_configuration()
        return pn532
    except RuntimeError:
        print("Card reader not initialized")
        time.sleep(5)
        machine.reset()


def check_card_reader():
    pass


def read_card(dev, tmot, config, relay, led_green, led_blue, led_red, syslog):
    try:
        GET_CARD_URL = "http://" + config['SERVER-IP'] + ":5001/api/v1/resources/get_card?card_id=" 
        UPDATE_CARD_URL = "http://" + config['SERVER-IP'] + ":5001/api/v1/resources/update_card"
        led_wait_on(led_green)
        print("Reading...")
        uid = dev.read_passive_target(timeout=tmot)
        if uid is None:
            print("CARD NOT FOUND")
        else:
            # TODO: replase whis blink code to funtion
            led_wait_off(led_green)
            led_reading(led_green)
            #led_card_found(led)
            numbers = [i for i in uid]
            string_ID = "{}{}{}{}".format(*numbers)
            print("Card number is {}".format(string_ID))
            syslog.info("Card number is {}".format(string_ID))
            req = requests.get(GET_CARD_URL + string_ID)
            card = json.loads(req.text)["data"][0]
            if card and card["daily_left"] > 0 and card["total_left"] > 0:
                # if выдано 2 порции day limit
                print("Loading....")
                syslog.info("Loading....")
                relay.off()
                time.sleep(float(config["RELAY-TIMER-{}".format(card["water_type"])]))  # задержка реле (время налива)
                relay.on()
                card["total_left"] -= 1
                card["daily_left"] -= 1
                card["realese_count"] += 1
                
                post_data = json.dumps(card) 
                syslog.info("Try to send update data for card {}".format(card))
                req = requests.post(UPDATE_CARD_URL, headers = {'content-type': 'application/json'}, data = post_data)
                syslog.info("OK")
            else:
                print('Card not in list or balance/day_limit is zero')
                led_warning(led_blue)
                syslog.warning("Card not in list or balance/day_limit is zero")
    except TypeError as err:
        print(err)
        led_error(led_red)


async def read_card_loop(reader, config, relay, led_green, led_blue, led_red, syslog):
    while True:
        try:
            read_card(reader, 500, config, relay, led_green, led_blue, led_red, syslog)
            await asyncio.sleep(3)
        except RuntimeError as err:
            print("Cannot get data from reader", err)
            led_error(led_red)
            syslog.error("Cannot get data from reader", err)
            time.sleep(5)
            machine.reset()
        except OSError as error:
            print("OSError {}".format(error))
            led_error(led_red)
            syslog.error("OSError {}".format(error))


def require_auth(func):
    config = load_config('config.json')

    def auth(req, resp):
        auth = req.headers.get(b"Authorization")
        if not auth:
            yield from resp.awrite(
                "HTTP/1.0 401 NA\r\n"
                'WWW-Authenticate: Basic realm="Picoweb Realm"\r\n'
                "\r\n"
            )
            return

        auth = auth.split(None, 1)[1]
        auth = ubinascii.a2b_base64(auth).decode()
        req.username, req.passwd = auth.split(":", 1)
        if not (
            (req.username == config["WEB-LOGIN"])
            and (req.passwd == config["WEB-PASSWORD"])
        ):
            yield from resp.awrite(
                "HTTP/1.0 401 NA\r\n"
                'WWW-Authenticate: Basic realm="Picoweb Realm"\r\n'
                "\r\n"
            )
            return

        yield from func(req, resp)

    return auth


def led_wait_on(led):
    led.duty(1023)


def led_wait_off(led):
    led.duty(0)


def led_reading(led):
    led.duty(511)
    time.sleep(2)
    led.duty(0)


def led_warning(led):
    led.duty(300)
    time.sleep(2)
    led.duty(0)


def led_error(led):
    led.duty(500)
    time.sleep(3) 
    led.duty(0)

