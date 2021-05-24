import gc
import machine
import NFC_PN532 as nfc
import picoweb
import uasyncio as asyncio
import ulogging as logging
import usyslog
import utime as time
from functions import (init_card_reader, ip_addr, load_config,
                       load_data, read_card, read_card_loop, require_auth,
                       save_config, save_data, set_config_handler,
                       set_limit_handler, add_card_handler)
from machine import Pin

logging.basicConfig(level=logging.INFO)

relay = Pin(18, Pin.OUT)
relay.on()
led = Pin(4, Pin.OUT)

pn532 = init_card_reader()

config = load_config("config.json")

sys_log = usyslog.UDPClient(ip=config["SYSLOG-SERVER-IP"])

app = picoweb.WebApp(__name__)


@app.route("/")
@require_auth
def send_index(req, resp):
    gc.collect()
    yield from app.sendfile(resp, "/www/index.html")


@app.route("/data.json")
def send_data(req, resp):
    gc.collect()
    yield from app.sendfile(resp, "data.json")


@app.route("/zepto.min.js")
def js(req, resp):
    gc.collect()
    yield from app.sendfile(resp, "/www/js/zepto.min.js")


@app.route("/config")
@require_auth
def get_config(req, resp):
    config = load_config("config.json")
    gc.collect()
    yield from app.render_template(resp, "config.html", (config,))


@app.route("/add_card")
@require_auth
def add_card(req, resp):
    if req.method == "GET":
        add_card_handler(req.qs)
        headers = {"Location": "/add_card"}
        gc.collect()
        yield from picoweb.start_response(resp, status="303", headers=headers)
    else:
        pass


@app.route("/send_config")
@require_auth
def send_config(req, resp):
    if req.method == "GET":
        set_config_handler(req.qs)
        headers = {"Location": "/config"}
        gc.collect()
        yield from picoweb.start_response(resp, status="303", headers=headers)
    else:  # GET, apparently
        pass


@app.route("/set_limit")
def set_limit(req, resp):
    if req.method == "GET":
        set_limit_handler(req.qs)
        headers = {"Location": "/"}
        gc.collect()
        yield from picoweb.start_response(resp, status="303", headers=headers)
    else:  # GET, apparently
        pass


loop = asyncio.get_event_loop()
loop.create_task(read_card_loop(pn532, config, relay, led, sys_log))

app.run(debug=1, host=ip_addr, port=80)

