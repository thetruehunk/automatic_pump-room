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

