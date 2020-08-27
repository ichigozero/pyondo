import sys
import time

import pigpio

from .dht import DhtSensor


def main():
    def _callback(data):
        print('{:.3f} {:2d} {} {:3.1f} {:3.1f} {:3.1f} {:3.1f} *'
              .format(*data))

    arg_count = len(sys.argv)

    if arg_count < 2:
        print("Need to specify at least one GPIO")
        sys.exit()

    pi = pigpio.pi()

    if not pi.connected:
        sys.exit()

    sensors = []

    for i in range(1, arg_count):
        gpio = int(sys.argv[i])

        if gpio >= 100:
            sensor = DhtSensor(
                pi=pi,
                gpio=gpio - 100,
                callback=_callback
            )
        else:
            sensor = DhtSensor(pi=pi, gpio=gpio)

        sensors.append((gpio, sensor))

    while True:
        try:
            for sensor in sensors:
                if sensor[0] >= 100:
                    sensor[1].read()
                else:
                    readings = sensor[1].read()
                    print('{:.3f} {:2d} {} {:3.1f} {:3.1f} {:3.1f} {:3.1f}'
                          .format(*readings))

            time.sleep(2)
        except KeyboardInterrupt:
            break

    for sensor in sensors:
        sensor[1].cancel()
        print("Cancelling {}".format(sensor[0]))

    pi.stop()


if __name__ == "__main__":
    main()
