import json
import logging
import sys
import time
import uuid

import click
import paho.mqtt.client as mqtt
import pigpio

from .dht import DhtSensor


@click.group()
def cmd():
    pass


@cmd.command()
@click.argument('gpios', nargs=-1, type=click.INT)
@click.option('--pause', '-p', default=2)
def test_run(gpios, pause):
    def _callback(data):
        print(
            'Timestamp:{:.3f} '
            'GPIO:{:2d} '
            'Status:{} '
            'T:{:3.1f} '
            'rH:{:3.1f} '
            'HI:{:3.1f} '
            'DP:{:3.1f}'
            .format(*data)
        )

    logging.basicConfig(level=logging.INFO)

    if not gpios:
        logging.error('Need to specify at least one GPIO')
        sys.exit()

    if pause < 2:
        logging.error('Pause time should be at least 2 seconds')
        sys.exit()

    pi = pigpio.pi()

    if not pi.connected:
        sys.exit()

    sensors = []

    for gpio in gpios:
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
                    print(
                        'Timestamp:{:.3f} '
                        'GPIO:{:2d} '
                        'Status:{} '
                        'T:{:3.1f} '
                        'rH:{:3.1f} '
                        'HI:{:3.1f} '
                        'DP:{:3.1f}'
                        .format(*readings)
                    )

            time.sleep(pause)
        except KeyboardInterrupt:
            break

    for sensor in sensors:
        sensor[1].cancel()
        logging.info('Cancelling %s', sensor[0])

    pi.stop()


@cmd.command()
@click.argument('gpio', type=click.INT)
@click.argument('broker')
@click.argument('topic')
@click.option('--pause', '-p', default=2)
@click.option('--verbose', '-v', is_flag=True)
def publish(gpio, broker, topic, pause, verbose):
    def _on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info('Connected to broker')
            client.connected_flag = True
        else:
            logging.error('Connection to broker failed')

    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    if pause < 2:
        logging.error('Pause time should be at least 2 seconds')
        sys.exit()

    pi = pigpio.pi()

    if not pi.connected:
        sys.exit()

    client = mqtt.Client('pyondo-{}'.format(uuid.uuid4()))
    client.on_connect = _on_connect
    client.connected_flag = False
    client.connect(broker)

    client.loop_start()
    retry_count = 0

    while not client.connected_flag:
        if retry_count < 5:
            time.sleep(1)
            retry_count += 1
        else:
            logging.error('Maximum retry count has been exceeded')
            sys.exit()

    sensor = DhtSensor(pi=pi, gpio=gpio)

    while True:
        try:
            readings = sensor.read()
            message = json.dumps({
                'temperature': readings.temperature,
                'humidity': readings.humidity,
                'heat_index': round(readings.heat_index, 2),
                'dew_point': round(readings.dew_point, 2),
            })

            client.publish(topic, message)
            logging.debug('Published message: %s', message)

            time.sleep(pause)
        except KeyboardInterrupt:
            break

    sensor.cancel()
    logging.info('Cancelling %s', gpio)

    client.disconnect()
    client.loop_stop()

    pi.stop()
