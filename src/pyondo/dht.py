import time
from math import log
from math import log10
from math import nan
from math import sqrt
from collections import namedtuple

import pigpio

DHT_AUTO = 0
DHT11 = 1
DHTXX = 2

DHT_GOOD = 0
DHT_BAD_CHECKSUM = 1
DHT_BAD_DATA = 2
DHT_TIMEOUT = 3


class DhtSensor:
    """
    A class to read the DHTXX temperature/humidity sensors.
    """
    def __init__(self, pi, gpio, model=DHT_AUTO, callback=None):
        """
        Instantiate with the Pi and the GPIO connected to the
        DHT temperature and humidity sensor.

        Optionally the model of DHT may be specified. It may be one
        of DHT11, DHTXX, or DHT_AUTO. It defaults to DHT_AUTO in which
        case the model of DHT is automtically determined.

        Optionally a callback may be specified. If specified the
        callback will be called whenever a new reading is available.

        The callback receives a tuple of timestamp, GPIO, status,
        temperature, and humidity.

        The timestamp will be the number of seconds since the epoch
        (start of 1970).

        The status will be one of:
        0 DHT_GOOD (a good reading)
        1 DHT_BAD_CHECKSUM (receieved data failed checksum check)
        2 DHT_BAD_DATA (data receieved had one or more invalid values)
        3 DHT_TIMEOUT (no response from sensor)
        """
        self._pi = pi
        self._gpio = gpio
        self._model = model
        self._callback = callback

        self._new_data = False
        self._in_code = False

        self._bits = 0
        self._code = 0

        self._status = DHT_TIMEOUT
        self._timestamp = time.time()
        self._temperature = 0.0
        self._humidity = 0.0
        self._Datum = namedtuple(
            'Datum',
            [
                'timestamp',
                'gpio',
                'status',
                'temperature',
                'humidity',
                'heat_index',
                'dew_point',
            ]
        )

        pi.set_mode(gpio=gpio, mode=pigpio.INPUT)
        self._last_edge_tick = pi.get_current_tick() - 10000
        self._callback_id = pi.callback(
            user_gpio=gpio,
            edge=pigpio.RISING_EDGE,
            func=self._rising_edge
        )

    def _rising_edge(self, _gpio, _level, tick):
        edge_length = pigpio.tickDiff(self._last_edge_tick, tick)
        self._last_edge_tick = tick

        if edge_length > 10000:
            self._in_code = True
            self._bits = -2
            self._code = 0
        elif self._in_code:
            self._bits += 1

            if self._bits >= 1:
                self._code <<= 1

                if 60 <= edge_length <= 150:
                    if edge_length > 100:
                        self._code += 1
                else:
                    self._in_code = False

            if self._in_code:
                if self._bits == 40:
                    self._decode_dhtxx()
                    self._in_code = False

    def _decode_dhtxx(self):
        """
              +-------+-------+
              | DHT11 | DHTXX |
              +-------+-------+
        Temp C| 0-50  |-40-125|
              +-------+-------+
        RH%   | 20-80 | 0-100 |
              +-------+-------+

                 0      1      2      3      4
              +------+------+------+------+------+
        DHT11 |check-| 0    | temp |  0   | RH%  |
              |sum   |      |      |      |      |
              +------+------+------+------+------+
        DHT21 |check-| temp | temp | RH%  | RH%  |
        DHT22 |sum   | LSB  | MSB  | LSB  | MSB  |
        DHT33 |      |      |      |      |      |
        DHT44 |      |      |      |      |      |
              +------+------+------+------+------+
        """
        byte0 = self._code & 0xff
        byte1 = self._code >> 8 & 0xff
        byte2 = self._code >> 16 & 0xff
        byte3 = self._code >> 24 & 0xff
        byte4 = self._code >> 32 & 0xff

        checksum = (byte1 + byte2 + byte3 + byte4) & 0xFF

        if checksum == byte0:
            if self._model == DHT11:
                valid_readings, temperature, humidity = (
                    self._validate_dht11(byte1, byte2, byte3, byte4))
            elif self._model == DHTXX:
                valid_readings, temperature, humidity = (
                    self._validate_dhtxx(byte1, byte2, byte3, byte4))
            else:
                valid_readings, temperature, humidity = (
                    self._validate_dhtxx(byte1, byte2, byte3, byte4))

                if not valid_readings:
                    valid_readings, temperature, humidity = (
                        self._validate_dht11(byte1, byte2, byte3, byte4))

            if valid_readings:
                self._temperature = temperature
                self._humidity = humidity
                self._status = DHT_GOOD
            else:
                self._status = DHT_BAD_DATA
        else:
            self._status = DHT_BAD_CHECKSUM

        self._new_data = True

    @classmethod
    def _validate_dht11(cls, byte1, byte2, byte3, byte4):
        temperature = byte2
        humidity = byte4

        valid_readings = (
            byte1 == 0 and
            byte3 == 0 and
            temperature <= 60 and
            9 <= humidity <= 90
        )

        return (valid_readings, temperature, humidity)

    @classmethod
    def _validate_dhtxx(cls, byte1, byte2, byte3, byte4):
        negative_temperature = byte2 & 128

        if negative_temperature:
            divisor = -10.0
        else:
            divisor = 10.0

        temperature = float(((byte2 & 127) << 8) + byte1) / divisor
        humidity = float((byte4 << 8) + byte3) / 10.0

        valid_readings = (
            humidity <= 110.0 and
            -50.0 <= temperature <= 135.0
        )

        return (valid_readings, temperature, humidity)

    def read(self):
        """
        This triggers a read of the sensor.

        The returned data is a tuple of timestamp, GPIO, status,
        temperature, and humidity.

        The timestamp will be the number of seconds since the epoch
        (start of 1970).

        The status will be one of:
        0 DHT_GOOD (a good reading)
        1 DHT_BAD_CHECKSUM (receieved data failed checksum check)
        2 DHT_BAD_DATA (data receieved had one or more invalid values)
        3 DHT_TIMEOUT (no response from sensor)
        """
        self._trigger()

        for _ in range(5):
            time.sleep(0.05)

            if self._new_data:
                break

        datum = self._Datum(
            timestamp=self._timestamp,
            gpio=self._gpio,
            status=self._status,
            temperature=self._temperature,
            humidity=self._humidity,
            heat_index=self.calculate_heat_index(
                self._temperature,
                self._humidity
            ),
            dew_point=self.calculate_dew_point(
                self._temperature,
                self._humidity
            ),
        )

        if self._callback is not None:
            self._callback(datum)

        return datum

    def _trigger(self):
        self._new_data = False
        self._timestamp = time.time()
        self._status = DHT_TIMEOUT

        self._pi.write(gpio=self._gpio, level=0)

        if self._model != DHTXX:
            time.sleep(0.018)
        else:
            time.sleep(0.001)

        self._pi.set_mode(gpio=self._gpio, mode=pigpio.INPUT)

    @staticmethod
    def calculate_heat_index(temperature, humidity):
        """
        Calculate heat index given celsius temperature and relative humidity.
        """
        def _to_fahrenheit(celsius):
            return (celsius * 1.8) + 32

        def _to_celsius(fahrenheit):
            return (fahrenheit - 32) / 1.8

        fahrenheit = _to_fahrenheit(temperature)

        heat_index = 0.5 * (
            fahrenheit
            + 61.0
            + ((fahrenheit - 68.0) * 1.2)
            + (humidity * 0.094)
        )

        if heat_index > 79:
            heat_index = (
                -42.379
                + 2.04901523 * fahrenheit
                + 10.14333127 * humidity
                - 0.22475541 * fahrenheit * humidity
                - 0.00683783 * pow(fahrenheit, 2)
                - 0.05481717 * pow(humidity, 2)
                + 0.00122874 * pow(fahrenheit, 2) * humidity
                + 0.00085282 * fahrenheit * pow(humidity, 2)
                - 0.00000199 * pow(fahrenheit, 2) * pow(humidity, 2)
            )

            if humidity < 13 and 80.0 <= fahrenheit <= 112.0:
                heat_index -= (
                    ((13.0 - humidity) * 0.25)
                    * sqrt((17.0 - abs(fahrenheit - 95.0)) / 17)
                )
            elif humidity > 85.0 and 80.0 <= fahrenheit <= 87.0:
                heat_index += (
                    ((humidity - 85.0) * 0.1)
                    * ((87.0 - fahrenheit) * 0.2)
                )

        return _to_celsius(heat_index)

    @staticmethod
    def calculate_dew_point(temperature, humidity):
        """
        Calculate dew point given celsius temperature and relative humidity.
        """
        if humidity < 1 or humidity > 100:
            return nan

        ratio = 373.15 / (273.15 + temperature)

        # Saturation Vapor Pressure (SVP)
        svp = -7.90298 * (ratio - 1)
        svp += 5.02808 * log10(ratio)
        svp += -1.3816e-7 * (pow(10, (11.344 * (1 - 1 / ratio))) - 1)
        svp += 8.1328e-3 * (pow(10, (-3.49149 * (ratio - 1))) - 1)
        svp += log10(1013.246)

        vapor_pressure = pow(10, svp - 3) * humidity
        vapor_temperature = log(vapor_pressure / 0.61078)

        return (241.88 * vapor_temperature) / (17.558 - vapor_temperature)

    def cancel(self):
        """
        Cancel registered callback
        """
        if self._callback_id is not None:
            self._callback_id.cancel()
            self._callback_id = None
