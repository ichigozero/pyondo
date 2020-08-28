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


@pytest.mark.parametrize(
    'dew_point', [
        10.0,
        12.9,
        pytest.param(9.9, marks=pytest.mark.xfail),
        pytest.param(13.0, marks=pytest.mark.xfail),
    ]
)
def test_turn_on_green_led(mocker, led_notifier_init, dew_point):
    spy_red_led = mocker.spy(led_notifier_init._leds.red, 'off')
    spy_amber_led = mocker.spy(led_notifier_init._leds.amber, 'off')
    spy_green_led = mocker.spy(led_notifier_init._leds.green, 'on')

    led_notifier_init.operate_leds(dew_point)

    spy_red_led.assert_called_once()
    spy_amber_led.assert_called_once()
    spy_green_led.assert_called_once()


@pytest.mark.parametrize(
    'dew_point', [
        13.0,
        15.9,
        pytest.param(12.9, marks=pytest.mark.xfail),
        pytest.param(16.0, marks=pytest.mark.xfail),
    ]
)
def test_blink_green_led(mocker, led_notifier_init, dew_point):
    spy_red_led = mocker.spy(led_notifier_init._leds.red, 'off')
    spy_amber_led = mocker.spy(led_notifier_init._leds.amber, 'off')
    spy_green_led = mocker.spy(led_notifier_init._leds.green, 'blink')

    led_notifier_init.operate_leds(dew_point)

    spy_red_led.assert_called_once()
    spy_amber_led.assert_called_once()
    spy_green_led.assert_called_once_with(on_time=1, off_time=1)


@pytest.mark.parametrize(
    'dew_point', [
        18.0,
        20.9,
        pytest.param(17.9, marks=pytest.mark.xfail),
        pytest.param(21.0, marks=pytest.mark.xfail),
    ]
)
def test_turn_on_amber_led(mocker, led_notifier_init, dew_point):
    spy_red_led = mocker.spy(led_notifier_init._leds.red, 'off')
    spy_amber_led = mocker.spy(led_notifier_init._leds.amber, 'on')
    spy_green_led = mocker.spy(led_notifier_init._leds.green, 'off')

    led_notifier_init.operate_leds(dew_point)

    spy_red_led.assert_called_once()
    spy_amber_led.assert_called_once()
    spy_green_led.assert_called_once()


@pytest.mark.parametrize(
    'dew_point', [
        16.0,
        17.9,
        pytest.param(15.9, marks=pytest.mark.xfail),
        pytest.param(18.0, marks=pytest.mark.xfail),
    ]
)
def test_blink_amber_led(mocker, led_notifier_init, dew_point):
    spy_red_led = mocker.spy(led_notifier_init._leds.red, 'off')
    spy_amber_led = mocker.spy(led_notifier_init._leds.amber, 'blink')
    spy_green_led = mocker.spy(led_notifier_init._leds.green, 'off')

    led_notifier_init.operate_leds(dew_point)

    spy_red_led.assert_called_once()
    spy_amber_led.assert_called_once_with(on_time=1, off_time=1)
    spy_green_led.assert_called_once()


@pytest.mark.parametrize(
    'dew_point', [
        24.0,
        pytest.param(23.9, marks=pytest.mark.xfail),
    ]
)
def test_turn_on_red_led(mocker, led_notifier_init, dew_point):
    spy_red_led = mocker.spy(led_notifier_init._leds.red, 'on')
    spy_amber_led = mocker.spy(led_notifier_init._leds.amber, 'off')
    spy_green_led = mocker.spy(led_notifier_init._leds.green, 'off')

    led_notifier_init.operate_leds(dew_point)

    spy_red_led.assert_called_once()
    spy_amber_led.assert_called_once()
    spy_green_led.assert_called_once()


@pytest.mark.parametrize(
    'dew_point', [
        9.9,
        21.0,
        23.9,
        pytest.param(10.0, marks=pytest.mark.xfail),
        pytest.param(20.9, marks=pytest.mark.xfail),
        pytest.param(24.0, marks=pytest.mark.xfail),
    ]
)
def test_blink_red_led(mocker, led_notifier_init, dew_point):
    spy_red_led = mocker.spy(led_notifier_init._leds.red, 'blink')
    spy_amber_led = mocker.spy(led_notifier_init._leds.amber, 'off')
    spy_green_led = mocker.spy(led_notifier_init._leds.green, 'off')

    led_notifier_init.operate_leds(dew_point)

    spy_red_led.assert_called_once_with(on_time=1, off_time=1)
    spy_amber_led.assert_called_once()
    spy_green_led.assert_called_once()
