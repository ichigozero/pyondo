import pytest


def test_assign_led(led_notifier, led_pins):
    assert led_notifier._leds is None

    led_notifier.assign_leds(led_pins)

    assert led_notifier._leds is not None


def test_assign_led_with_invalid_pins(led_notifier):
    assert led_notifier._leds is None

    invalid_pins = {'red': '', 'amber': '', 'green': ''}
    led_notifier.assign_leds(invalid_pins)

    assert led_notifier._leds is None


def test_close_led_before_reassignment(mocker, led_notifier_init, led_pins):
    spy = mocker.spy(led_notifier_init._leds, 'close')
    led_notifier_init.assign_leds(led_pins)

    spy.assert_called_once()
