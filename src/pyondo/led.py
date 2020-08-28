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
