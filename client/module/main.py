import gc
import sys
import machine
import NFC_PN532 as nfc
import picoweb
import uasyncio as asyncio
import usyslog
import utime as time
from functions import (init_card_reader, load_config, read_card, read_card_loop, require_auth,
                       set_config_handler, feed_watchdog)
from machine import Pin, WDT, PWM



relay = Pin(18, Pin.OUT)
relay.on()

led = Pin(4, Pin.OUT)

led_blue = PWM(Pin(26), freq=1, duty=0)
led_green = PWM(Pin(25), freq=1, duty=0)
led_red = PWM(Pin(33), freq=1, duty=0)

pn532 = init_card_reader()

config = load_config("config.json")

syslog = usyslog.UDPClient(ip=config["SYSLOG-SERVER-IP"])

app = picoweb.WebApp(__name__)

wdt = WDT(timeout=15000)
wdt.feed()


@app.route("/")
@require_auth
def get_config(req, resp):
    config = load_config("config.json")
    gc.collect()
    yield from app.render_template(resp, "index.html", (config,))
    syslog.info("Picoweb: requested page 'index.html'")


@app.route("/send_config")
@require_auth
def send_config(req, resp):
    if req.method == "GET":
        set_config_handler(req.qs)
        headers = {"Location": "/"}
        gc.collect()
        yield from picoweb.start_response(resp, status="303", headers=headers)
        syslog.info("Picoweb: send config")
        # TODO Show message about reboot 
        machine.reset()
    else:  # GET, apparently
        pass


loop = asyncio.get_event_loop()
loop.create_task(read_card_loop(pn532, config, relay, led_green, led_blue, led_red, syslog))
loop.create_task(feed_watchdog(wdt))

try:
    app.run(debug=1, host="0.0.0.0", port=80)
except KeyboardInterrupt:
        wdt = WDT(timeout=3600000)
        wdt.feed()
        print("Aborted through keyboard")

