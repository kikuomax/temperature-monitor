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
