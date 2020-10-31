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
        sensor = DhtSensor(pi=pi, gpio=gpio, callback=_callback)
        sensors.append((gpio, sensor))

    while True:
        try:
            for sensor in sensors:
                sensor[1].read()

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
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    if pause < 2:
        logging.error('Pause time should be at least 2 seconds')
        sys.exit()

    pi = pigpio.pi()

    if not pi.connected:
        sys.exit()

    def _on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info('Connected to broker')
            client.connected_flag = True
        else:
            logging.error('Connection to broker failed')

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

    def _callback(data):
        message = json.dumps({
            'temperature': data.temperature,
            'humidity': data.humidity,
            'heat_index': round(data.heat_index, 2),
            'dew_point': round(data.dew_point, 2),
        })

        client.publish(topic, message)
        logging.debug('Published message: %s', message)

    sensor = DhtSensor(pi=pi, gpio=gpio, callback=_callback)

    while True:
        try:
            sensor.read()
            time.sleep(pause)
        except KeyboardInterrupt:
            break

    sensor.cancel()
    logging.info('Cancelling %s', gpio)

    client.disconnect()
    client.loop_stop()

    pi.stop()
