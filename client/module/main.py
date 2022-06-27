import gc
import machine
import picoweb
import uasyncio as asyncio
import usyslog
from functions import (
        load_config,
        require_auth,
        set_config_handler,
        feed_watchdog
        )
from controller import Pump


config = load_config("config.json")

syslog = usyslog.UDPClient(ip=config["SYSLOG-SERVER-IP"])

pump = Pump()
pump.syslog = syslog
pump.init_card_reader()

app = picoweb.WebApp(__name__)

wdt = machine.WDT(timeout=15000)
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
    if req.method == "POST":
        yield from req.read_form_data()
        set_config_handler(req.form)
        headers = {"Location": "/"}
        gc.collect()
        yield from picoweb.start_response(resp, status="303", headers=headers)
        syslog.info("Picoweb: send config")
        # TODO Show message about reboot 
        machine.reset()
    else:  # GET, apparently
        pass


loop = asyncio.get_event_loop()
loop.create_task(pump.read_card_loop())
loop.create_task(feed_watchdog(wdt))

try:
    app.run(debug=1, host="0.0.0.0", port=80)
except KeyboardInterrupt:
        wdt = machine.WDT(timeout=3600000)
        wdt.feed()
        print("Aborted through keyboard")

