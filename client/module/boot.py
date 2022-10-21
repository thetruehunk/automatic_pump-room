import esp
import gc
import webrepl
import wireless

#esp.osdebug(None)
wireless.activate()
webrepl.start()
gc.collect()

