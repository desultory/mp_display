from utime import ticks_ms, ticks_diff
from machine import Pin


class Button:
    def __init__(self, pin, pull_down=True, debounce=250):
        self.debounce = debounce
        self.last = ticks_ms()
        if pull_down:
            self.pin = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        else:
            self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self._callback)
        self._value = False

    def _callback(self, pin):
        self._value = True

    @property
    def value(self):
        if ticks_diff(ticks_ms(), self.last) < self.debounce:
            return False
        if self._value:
            self.last = ticks_ms()
            self._value = False
            return True
        return False
