# About

Raspberry Pi temperature monitor with DHT11/22 sensor.

# Installation

```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install .
```

# Wiring

See below diagram for wiring reference.

![dht22-wiring](/diagram/dht22_wiring.jpg)

# Usage

## Printing sensor output to console only

```bash
$ pyondo test-run [OPTIONS] [GPIOS]
```

Run the following command to read sensors connected to GPIO 4 and 7.

```bash
$ pyondo test-run 4 7
```

### OPTIONS

```
   -h, --help                       Print this help text and exit
   -p, --pause                      Pause interval in seconds between readings.
                                    Must be 2 seconds or more
```

## Publish sensor output to Mosquitto broker

```bash
$ pyondo publish [OPTIONS] GPIO BROKER TOPIC
```

Run the following command to publish reading of sensor connected to GPIO 4
to local broker with topic home/dht22

```bash
$ pyondo publish 4 127.0.0.1 "home/dht22"
```

### OPTIONS

```
   -h, --help                       Print this help text and exit
   -p, --pause                      Pause interval in seconds between readings.
                                    Must be 2 seconds or more
   -s, --status                     Only publish reading with the same or
                                    status code or lower.
                                    0: Good reading
                                    1: Bad checksum reading
                                    2: Bad data reading
   -v, --verbose                    Print output in verbose mode
```

# Credit

- [abyz.me.uk](http://abyz.me.uk/rpi/pigpio/index.html) for the original code
