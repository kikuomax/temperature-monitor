# Monitoring Temperature and Humidity with DHT22 on Raspberry Pi Zero W

Remarks,
- Actually I got a Raspberry Pi Zero WH which has a GPIO hat soldered.
- I got a sensor labeled as AM2302 but it is essentially a DHT22.

## Getting a Raspberry Pi Zero W Connected via WiFi without a Monitor

I did OS image installation on OSX.

[This page](https://www.raspberrypi.org/documentation/installation/installing-images/mac.md) explains basic operations for making an OS image on OSX.

[This page](https://www.losant.com/blog/getting-started-with-the-raspberry-pi-zero-w-without-a-monitor) was so helpful.
Note that double quotes surrounding SSID and password in the following example of `wpa_supplicant.conf` are not just there for emphasis, but you have to actually surround them with double quotes.

```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
 ssid="WIFI_SSID" <-- not just for emphasis
 scan_ssid=1
 psk="WIFI_PASSWORD" <-- not just for emphasis
 key_mgmt=WPA-PSK
}
```

By the way, I live in Japan, so I replaced `country=US` with `country=JP`.

## Wiring DHT22 and Raspberry Pi Zero W

The [GPIO layout](https://www.raspberrypi.org/documentation/usage/gpio/) for your reference.

I followed the wiring instruction on [this page](https://www.hackster.io/adamgarbo/raspberry-pi-2-iot-thingspeak-dht22-sensor-b208f4).

I used [Adafruit_Python_DHT](https://github.com/adafruit/Adafruit_Python_DHT) for testing as described on [this page](https://tutorials-raspberrypi.com/raspberry-pi-measure-humidity-temperature-dht11-dht22/).
Because my sensor was AM2302 (i.e., DHT22) and the data pin was connected to GPIO17, I ran the following command (sensor type = 22 also worked),
```shell
$ sudo python AdafruitDHT.py 2302 17
Temp=23.0*  Humidity=55.3%
```

## Obtaining Data via `pigpiod`

`pigpiod` allows you to access GPIO without the root privilege.

The following conversation helped me,
- [This](https://www.raspberrypi.org/forums/viewtopic.php?t=182734) to install `pigpiod`
- [This](https://www.raspberrypi.org/forums/viewtopic.php?f=32&t=103752) to run `pigpiod` at start-up of my Raspberry Pi
- [This](https://www.raspberrypi.org/forums/viewtopic.php?t=199323) to test whether `pigpiod` is running

You can get an example of how to get data from DHT22 via `pigpiod` from [here](http://abyz.me.uk/rpi/pigpio/examples.html#Python_DHT22_py).

I edited the example code `DHT22.py` so that it communicates through GPIO17 (neither LED nor power).
```python
s = DHT22.sensor(pi, 17)
```

By running the modified [`src/DHT22.py`](src/DHT22.py), I got the following results,
```shell
$ python DHT22.py
1 54.6 23.2 0.17 0 0 0 0
2 55.1 23.1 0.18 0 0 0 0
3 55.4 23.1 0.18 0 0 0 0
4 55.2 23.1 0.18 0 0 0 0
...
```
