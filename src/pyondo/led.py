from gpiozero import TrafficLights
from gpiozero.exc import PinInvalidPin


def _ignore_exception(function):
    def wrapper(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except AttributeError:
            pass

    return wrapper


class LedNotifier:
    def __init__(self, led_pins=None):
        self._leds = None

        self.assign_leds(led_pins)

    @_ignore_exception
    def assign_leds(self, led_pins):
        self._close_leds()

        try:
            self._leds = TrafficLights(
                red=led_pins.get('red'),
                amber=led_pins.get('amber'),
                green=led_pins.get('green')
            )
        except PinInvalidPin:
            pass

    @_ignore_exception
    def _close_leds(self):
        self._leds.close()

    @_ignore_exception
    def operate_leds(self, dew_point, on_time=1, off_time=1):
        if dew_point < 10.0:
            self._leds.red.blink(on_time, off_time)
            self._leds.amber.off()
            self._leds.green.off()
        elif 10.0 <= dew_point < 16.0:
            if 10.0 <= dew_point < 13.0:
                self._leds.green.on()
            else:
                self._leds.green.blink(on_time, off_time)

            self._leds.red.off()
            self._leds.amber.off()
        elif 16.0 <= dew_point < 21.0:
            if 16.0 <= dew_point < 18.0:
                self._leds.amber.blink(on_time, off_time)
            else:
                self._leds.amber.on()

            self._leds.red.off()
            self._leds.green.off()
        elif dew_point >= 21.0:
            if 21.0 <= dew_point < 24.0:
                self._leds.red.blink(on_time, off_time)
            else:
                self._leds.red.on()

            self._leds.amber.off()
            self._leds.green.off()
