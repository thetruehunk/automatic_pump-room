import utime as time
import machine
import uasyncio as asyncio
from machine import Pin, SoftSPI
import NFC_PN532 as nfc
import urequests as requests
import json
from functions import load_config
import ulogging


class Pump:

    syslog: object
    logger: object
    reader: object

    def led_wait_on(self):
        self.led_green.on()
    
    def led_wait_off(self):
        self.led_green.off()
    
    def led_reading(self):
        for _ in range(4):
            self.led_green.on()
            time.sleep(0.2)
            self.led_green.off()
            time.sleep(0.2)
    
    def led_warning(self):
        self.led_blue.on()
        self.led_green.on()
        time.sleep(2)
        self.led_blue.off()
        self.led_green.off()
    
    def led_error(self):
        self.led_red.on()

    def info_logging(self, template, *args):
        prefix = 'ID: ' + self.config["CLIENT-ID"] + ': ' 
        if args is None:
            ulogging.info(template)
            self.syslog.info(prefix + template)
        else:
            ulogging.info(template.format(*args))
            self.syslog.info(prefix + template.format(*args))
    
    def error_logging(self, template, *args):
        prefix = 'ID: ' + self.config["CLIENT-ID"] + ': ' 
        if args is None:
            ulogging.error(template)
            self.syslog.error(prefix + template)
        else:
            ulogging.error(template.format(*args))
            self.syslog.error(prefix + template.format(*args))

    def init_card_reader(self):
        try:
            spi_dev = SoftSPI(
                baudrate=1000000, sck=self.sck, mosi=self.mosi, miso=self.miso
            )
            self.cs.on()
            self.reader = nfc.PN532(spi_dev, self.cs)
            ic, ver, rev, support = self.reader.get_firmware_version()
            self.info_logging("Found PN532 with firmware version: {0}.{1}", ver, rev)
            self.reader.SAM_configuration()
        except RuntimeError:
            self.error_logging("Card reader not initialized")
            self.led_error()
            time.sleep(5)

    def check_card_reader():
        pass

    def read_card(self):
        try:
            GET_CARD_URL = (
                "http://"
                + self.config["SERVER-IP"]
                + ":5001/api/v1/resources/get_card?card_id="
            )
            UPDATE_CARD_URL = (
                "http://"
                + self.config["SERVER-IP"]
                + ":5001/api/v1/resources/update_card"
            )
            self.led_wait_on()
            print("Reading...")
            uid = self.reader.read_passive_target(timeout=500)
            if uid is None:
                print("CARD NOT FOUND")
            else:
                self.led_wait_off()
                self.led_reading()
                numbers = [i for i in uid]
                string_ID = "{}{}{}{}".format(*numbers)
                self.info_logging("Card number is {}", string_ID)
                req = requests.get(GET_CARD_URL + string_ID)
                card = json.loads(req.text)["data"][0]
                if card and card["daily_left"] > 0 and card["total_left"] > 0:
                    self.info_logging("Loading....")
                    self.relay.off()
                    time.sleep(
                        float(self.config["RELAY-TIMER-{}".format(card["water_type"])])
                    )
                    # задержка реле (время налива)
                    self.relay.on()
                    card["total_left"] -= 1
                    card["daily_left"] -= 1
                    card["realese_count"] += 1

                    post_data = json.dumps(card)
                    self.info_logging("Try to send update data for card {}", card)
                    req = requests.post(
                        UPDATE_CARD_URL,
                        headers={"content-type": "application/json"},
                        data=post_data,
                    )
                    self.info_logging("Update is success")
                else:
                    self.info_logging("Card not in list or balance/day_limit is zero")
                    self.led_warning()
        except TypeError as err:
            self.error_logging(err)
            self.led_error()

    async def read_card_loop(self):
        while True:
            try:
                self.read_card()
                await asyncio.sleep(1)
            except RuntimeError as err:
                self.error_logging("Cannot get data from reader", err)
                self.led_error()
                time.sleep(5)
                machine.reset()
            except OSError as err:
                self.error_logging("OSError {}", err)
                self.led_error()

    def __init__(
        self,
        sck=5,
        cs=22,
        mosi=23,
        miso=19,
        relay=18,
        led_blue=26,
        led_green=25,
        led_red=33,
    ):
        # SPI
        self.sck = Pin(sck)
        self.cs = Pin(cs, Pin.OUT)
        self.mosi = Pin(mosi)
        self.miso = Pin(miso)
        # Relay
        self.relay = Pin(relay, Pin.OUT)
        self.relay.on()
        # RGB led
        self.led_blue = Pin(led_blue, Pin.OUT)
        self.led_green = Pin(led_green, Pin.OUT)
        self.led_red = Pin(led_red, Pin.OUT)
        # Config
        self.config = load_config("config.json")
