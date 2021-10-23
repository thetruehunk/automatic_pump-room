import gc
import machine
import NFC_PN532 as nfc
import picoweb
import uasyncio as asyncio
import usyslog
import utime as time
from functions import (init_card_reader, load_config, read_card, read_card_loop, require_auth,
                       set_config_handler, feed_watchdog)
from machine import Pin, WDT



relay = Pin(18, Pin.OUT)
relay.on()
led = Pin(4, Pin.OUT)

pn532 = init_card_reader()

config = load_config("config.json")

syslog = usyslog.UDPClient(ip=config["SYSLOG-SERVER-IP"])

app = picoweb.WebApp(__name__)

wdt = WDT()
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
loop.create_task(read_card_loop(pn532, config, relay, led, syslog))
loop.create_task(feed_watchdog(wdt))

app.run(debug=1, host="0.0.0.0", port=80)

