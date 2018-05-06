# Monitoring Temperature and Humidity with DHT22 on Raspberry Pi Zero W

Remarks,
- This documentation just describes what I did and is not intended to provide you with instructions, but may give you some hints.
- Actually, I got a Raspberry Pi Zero WH which has a GPIO hat soldered.
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

## Publishing Temperature and Humidity Through MQTT

[This page](https://learn.adafruit.com/diy-esp8266-home-security-with-lua-and-mqtt/configuring-mqtt-on-the-raspberry-pi) helped me get started.
But note that `python-mosquitto` referenced there has been replaced by [`paho`](https://eclipse.org/paho/clients/python/).

### Eclipse Mosquitto

[Eclipse Mosquitto](https://mosquitto.org) provides MQTT broker and clients.
You can find basic usage at [its GitHub repository](https://github.com/eclipse/mosquitto).

### Learning steps

To learn MQTT, I took the following steps,
1. [Test an MQTT broker without TLS](#step-1-testing-an-mqtt-broker-without-tls)
2. [Test an MQTT broker with TLS and a broker certificate](#step-2-testing-an-mqtt-broker-with-tls-and-a-broker-certificate)
3. [Test an MQTT broker with TLS, and broker and client certificates](#step-3-testing-an-mqtt-broker-with-tls-and-broker-and-client-certificates)

### Step 1: testing an MQTT broker without TLS

#### Installing and running an MQTT broker

I installed and ran an MQTT broker on OSX.

```
brew install mosquitto
brew services start mosquitto
```

#### Publishing through MQTT without TLS

I added the following changes to [`src/DHT22.py`](src/DHT22.py) and saved it as [`src/DHT22_mqtt.py`](src/DHT22_mqtt.py).

- Connection to an MQTT broker.

  `Pittsburgh.local` is the name of my local machine.
  An MQTT broker is listening at the port `1883` by default.

  ```python
  import paho.mqtt.client as mqtt
  mqtt_client = mqtt.Client()
  mqtt_client.connect('Pittsburgh.local', port=1883, keepalive=60)
  mqtt_client.loop_start()
  ```

- Publishing a message via MQTT

  ```python
  payload = "{} {} {} {:3.2f} {} {} {} {}".format(
      r, s.humidity(), s.temperature(), s.staleness(),
      s.bad_checksum(), s.short_message(), s.missing_message(),
      s.sensor_resets())
  message_info = mqtt_client.publish(
      'monitor/temperature-and-humidity',
      payload,
      qos=0)
  print('rc: {}'.format(message_info.rc))
  ```

I ran [`src/DHT22_mqtt.py`](src/DHT22_mqtt.py) on my Raspberry Pi.
It started publishing messages to the topic `monitor/temperature-and-humidity` while printing the following messages,

```
$ python DHT22_mqtt_no_tls.py
rc: 0
1 58.2 24.1 0.17 0 0 0 0
rc: 0
2 59.0 24.2 0.18 0 0 0 0
...
```

#### Subscribing MQTT messages

MQTT messages can be subscribed with the `mosquitto_sub` command.

I ran `mosquitto_sub` on my local machine, and it printed the following messages,

```
$ mosquitto_sub -h Pittsburgh.local -t monitor/temperature-and-humidity
11 59.1 24.1 0.18 0 0 0 0
12 59.1 24.1 0.18 0 0 0 0
...
```

### Step 2: testing an MQTT broker with TLS and a broker certificate

#### Generating a private root certificate authority for secure communication

A certificate authority is necessary to sign broker and client certificates.

I tried to follow [the `test/ssl/gen.sh` file in Moqsuitto's GitHub repository](https://github.com/eclipse/mosquitto/blob/master/test/ssl/gen.sh), but I could not make it.

Then I followed the steps described on [this page](http://www.steves-internet-guide.com/mosquitto-tls/), and it worked.

The following are the steps I actually took,

1. Generate a CA key

    ```
    openssl genrsa -des3 -out root-ca.key 2048
    ```

2. Generate a certificate for the CA

    ```
    openssl req -new -x509 -days 36500 -key root-ca.key -out root-ca.crt
    ```
    I supplied the following attributes,
    ```
    Country Name (2 letter code) []:JP
    State or Province Name (full name) []:Kanagawa
    Locality Name (eg, city) []:Atsugi
    Organization Name (eg, company) []:Emoto
    Organizational Unit Name (eg, section) []:Root CA
    Common Name (eg, fully qualified host name) []:Root CA
    Email Address []:x@y.z
    ```

#### Signing a broker certificate

Basic commands to sign broker and client certificates are described [here](https://mosquitto.org/man/mosquitto-tls-7.html).

NOTE: As described on [this page](http://www.steves-internet-guide.com/mosquitto-tls/), you cannot use the same attributes for a broker certificate as those for the CA certificate.

I actually took the following steps,

1. Generate a key for the broker

    ```
    openssl genrsa -out mqtt-broker.key 2048
    ```

2. Generate a certificate signing request for the broker

    ```
    openssl req -out mqtt-broker.csr -key mqtt-broker.key -new
    ```
    I supplied the following attributes,
    ```
    Country Name (2 letter code) []:JP
    State or Province Name (full name) []:Kanagawa
    Locality Name (eg, city) []:Atsugi
    Organization Name (eg, company) []:Emoto
    Organizational Unit Name (eg, section) []:MQTT Broker
    Common Name (eg, fully qualified host name) []:Pittsburgh.local
    Email Address []:x@y.z

    Please enter the following 'extra' attributes
    to be sent with your certificate request
    A challenge password []:      
    ```

3. Sign the certificate of the broker with the root CA

    ```
    openssl x509 -req -in mqtt-broker.csr -CA root-ca.crt -CAkey root-ca.key -CAcreateserial -out mqtt-broker.crt -days 36500
    ```

#### Configuring mosquitto to use the broker certificate

I basically followed the instructions described [here](http://www.steves-internet-guide.com/mosquitto-tls/).

I added the following properties to the `mosquitto.conf` on my local machine.
Because I installed `mosquitto` to my local machine via [Homebrew](https://brew.sh), it is located at `/usr/local/etc/mosquitto/mosquitto.conf`.

```
# local name of my machine
bind_address Pittsburgh.local

# standard port for secure MQTT
port 8883

# CA certificate generated in the subsection "Generating a private root certificate authority for secure communication"
cafile /Users/kikuo/Documents/projects/temperature-monitor/cert/root-ca.crt

# broker certificate generated in the subsection "Signing a broker certificate"
certfile /Users/kikuo/Documents/projects/temperature-monitor/cert/mqtt-broker.crt

# broker certificate key generated in the subsection "Signing a broker certificate"
keyfile /Users/kikuo/Documents/projects/temperature-monitor/cert/mqtt-broker.key

# maybe TLSv1.2 is preferable
tls_version tlsv1.2
```

Then I restarted mosquitto.

```
brew services restart mosquitto
```

#### Publishing through MQTT with TLS and a broker certificate

An MQTT client needs the root CA certificate to verify the MQTT broker, so I copied `root-ca.crt` to my Raspberry Pi.

I added the following changes to [`src/DHT22_mqtt.py`](src/DHT22_mqtt.py) and saved it as [`src/DHT22_mqtt_crt_broker.py`](src/DHT22_mqtt_crt_broker.py).

- Importation of the `ssl` module

  ```python
  import ssl
  ```

- Configuration of the root CA certificate before connecting to the MQTT broker

  ```python
  mqtt_client.tls_set(
      ca_certs='/home/pi/projects/temperature-monitor/cert/root-ca.crt',
      cert_reqs=ssl.CERT_REQUIRED,
      tls_version=ssl.PROTOCOL_TLSv1_2)
  mqtt_client.connect('Pittsburgh.local', port=8883, keepalive=60)
  ```

I ran [`src/DHT22_mqtt_crt_broker.py`](src/DHT22_mqtt_crt_broker.py) on my Raspberry Pi.
After getting some errors, it finally started publishing messages to the topic `monitor/temperature-and-humidity`.

The main error I got was a certificate verification error.
When my certificate was wrong, I got the following error,

```
Traceback (most recent call last):
  File "DHT22_mqtt_crt_broker.py", line 257, in <module>
    mqtt_client.connect('Pittsburgh.local', port=8883, keepalive=60)
  File "/usr/local/lib/python2.7/dist-packages/paho/mqtt/client.py", line 768, in connect
    return self.reconnect()
  File "/usr/local/lib/python2.7/dist-packages/paho/mqtt/client.py", line 927, in reconnect
    sock.do_handshake()
  File "/usr/lib/python2.7/ssl.py", line 840, in do_handshake
    self._sslobj.do_handshake()
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:661)
```

#### Subscribing MQTT messages with TLS and a broker certificate

Because the MQTT broker uses TLS for every communication, `mosquitto_sub` also needs the root CA certificate.

I ran the following command to subscribe MQTT messages,

```
mosquitto_sub -h Pittsburgh.local -p 8883 -t monitor/temperature-and-humidity --cafile root-ca.crt
```

### Step 3: testing an MQTT broker with TLS, and broker and client certificates

#### Signing client certificates

I prepared two client certificates, one for my Raspberry Pi publishing temperature and humidity reading (sensor) and the other for my local machine subscribing them (subscriber).

When I signed second and subsequent certificates, I replaced `-CAcreateserial` with `-CAserial root-ca.srl`.
`root-ca.srl` was generated when the broker certificate was signed with the `-CAcreateserial` option.

Steps to sign a sensor certificate,

1. Generate a key for the sensor

    ```
    openssl genrsa -out mqtt-sensor-1.key 2048
    ```

2. Generate a certificate signing request for the sensor

    ```
    openssl req -out mqtt-sensor-1.csr -key mqtt-sensor-1.key -new
    ```
    I supplied the following attributes,
    ```
    Country Name (2 letter code) []:JP
    State or Province Name (full name) []:Kanagawa
    Locality Name (eg, city) []:Atsugi
    Organization Name (eg, company) []:Emoto
    Organizational Unit Name (eg, section) []:MQTT Sensor  
    Common Name (eg, fully qualified host name) []:raspberrypi.local
    Email Address []:x@y.z

    Please enter the following 'extra' attributes
    to be sent with your certificate request
    A challenge password []:
    ```

3. Sign the certificate of the sensor

    ```
    openssl x509 -req -in mqtt-sensor-1.csr -CA root-ca.crt -CAkey root-ca.key -CAserial root-ca.srl -out mqtt-sensor-1.crt -days 36500
    ```

I copied `mqtt-sensor-1.crt` and `mqtt-sensor-1.key` to my Raspberry Pi.

Steps to sign a subscriber certificate (quite similar to the steps for the sensor),

1. Generate a key for the subscriber

    ```
    openssl genrsa -out mqtt-subscriber-1.key 2048
    ```

2. Generate a certificate signing request for the subscriber

    ```
    openssl req -out mqtt-subscriber-1.csr -key mqtt-subscriber-1.key -new
    ```
    I supplied the following attributes,
    ```
    Country Name (2 letter code) []:JP
    State or Province Name (full name) []:Kanagawa
    Locality Name (eg, city) []:Atsugi
    Organization Name (eg, company) []:Emoto
    Organizational Unit Name (eg, section) []:MQTT Subscriber
    Common Name (eg, fully qualified host name) []:Pittsburgh.local
    Email Address []:x@y.z

    Please enter the following 'extra' attributes
    to be sent with your certificate request
    A challenge password []:
    ```

3. Sign the certificate of the subscriber

    ```
    openssl x509 -req -in mqtt-subscriber-1.csr -CA root-ca.crt -CAkey root-ca.key -CAserial root-ca.srl -out mqtt-subscriber-1.crt -days 36500
    ```

#### Configuring mosquitto to authenticate clients with certificates

I added the following properties to the `mosquitto.conf` on my local machine and restarted mosquitto.

```
require_certificate true
```

#### Publishing through MQTT with TLS and a client certificate

An MQTT client needs its certificate to be authenticated in addition to the root CA certificate.

I added the following changes to [`src/DHT22_mqtt_crt_broker.py`](src/DHT22_mqtt_crt_broker.py) and saved it as [`src/DHT22_mqtt_crt_both.py`](src/DHT22_mqtt_crt_both.py).

- Addition of the client certificate and key
  ```
  mqtt_client.tls_set(
      ca_certs='/home/pi/projects/temperature-monitor/cert/root-ca.crt',
      # client certificate
      certfile='/home/pi/projects/temperature-monitor/cert/mqtt-sensor-1.crt',
      # client key
      keyfile='/home/pi/projects/temperature-monitor/cert/mqtt-sensor-1.key',
      cert_reqs=ssl.CERT_REQUIRED,
      tls_version=ssl.PROTOCOL_TLSv1_2)
  ```

I ran [`src/DHT22_mqtt_crt_both.py`](src/DHT22_mqtt_crt_both.py) on my Raspberry Pi.

#### Subscribing MQTT messages with TLS and a client certificate

Because the MQTT broker requires to every client its certificate, a subscriber also needs its certificate.

I ran the following command to subscribe MQTT messages,

```
mosquitto_sub -h Pittsburgh.local -p 8883 -t monitor/temperature-and-humidity --cafile root-ca.crt --cert mqtt-subscriber-1.crt --key mqtt-subscriber-1.key
```

## AWS IoT

To scale my service, I decided to migrate to [AWS IoT](https://aws.amazon.com/iot/).

First, I replaced the MQTT broker with the equivalent of AWS (AWS Message Broker).
Then I implemented a Web page subscribing messages via MQTT over WebSocket.

### Creating things

To access the AWS Message Broker, I had to [create a thing](https://docs.aws.amazon.com/iot/latest/developerguide/register-device.html) first.

#### Creating a thing representing the Raspberry Pi

I took the following steps,

1. Create a thing (`temperature-sensor-1`)

2. Create certificates for the thing `temperature-sensor-1`

    1. Download the following files
        - `XYZ-certificate.pem.crt`
        - `XYZ-private.pem.crt`
        - The root CA certificate issued by Symantec
    2. Copy the above files to my Raspberry Pi

3. Create a policy `temperature-sensor` similar to the following,
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": "iot:Connect",
          "Resource": "arn:aws:iot:ap-northeast-1:AWS-ACCOUNT-ID:client/*"
        },
        {
          "Effect": "Allow",
          "Action": "iot:Publish",
          "Resource": "arn:aws:iot:ap-northeast-1:AWS-ACCOUNT-ID:topic/home/temperature-and-humidity"
        }
      ]
    }
    ```

4. Attach the policy `temperature-sensor` to the thing `temperature-sensor-1`

#### Creating a thing representing a subscriber

I took the following steps,

1. Create a thing (`home-monitor`)

2. Create certificates for the thing `home-monitor`

    Download the following files,
    - `XYZ-certificate.pem.crt`
    - `XYZ-private.pem.crt`
    - The root CA certificate issued by Symantec (NOTE: the same as that downloaded in the previous subsubsection)

3. Create a policy `home-monitor` similar to the following,
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": "iot:Connect",
          "Resource": "arn:aws:iot:ap-northeast-1:AWS-ACCOUNT-ID:client/*"
        },
        {
          "Effect": "Allow",
          "Action": "iot:Receive",
          "Resource": "arn:aws:iot:ap-northeast-1:AWS-ACCOUNT-ID:topic/home/*"
        },
        {
          "Effect": "Allow",
          "Action": "iot:Subscribe",
          "Resource": "arn:aws:iot:ap-northeast-1:AWS-ACCOUNT-ID:topicfilter/home/*"
        }
      ]
    }
    ```

4. Attach the policy `home-monitor` to the thing `home-monitor`

**NOTE: I could not subscribe the topic `home/temperature-and-humidity` without `iot:Receive` allowed.**

### Publishing messages to the AWS Message Broker

Because I already introduced an MQTT broker in the previous section, it was very straight forward to publish messages to the AWS Message Broker.

I added the following changes to [`src/DHT22_mqtt_crt_both.py`](src/DHT22_mqtt_crt_both.py) and saved it as [`src/DHT22_aws_iot.py`](src/DHT22_aws_iot.py).

- Configurations
  ```python
  import os
  mqtt_host_name = os.environ['MQTT_HOST_NAME']
  mqtt_port = 8883
  topic_to_publish = 'home/temperature-and-humidity'
  ```

- TLS parameters for the AWS Message Broker
  ```python
  mqtt_client.tls_set(
      ca_certs='/home/pi/projects/temperature-monitor/aws-iot/root-ca.pem',
      certfile='/home/pi/projects/temperature-monitor/aws-iot/mqtt-sensor-1.pem.crt',
      keyfile='/home/pi/projects/temperature-monitor/aws-iot/mqtt-sensor-1.private.key',
      cert_reqs=ssl.CERT_REQUIRED,
      tls_version=ssl.PROTOCOL_TLSv1_2)
  ```

- Connection using the configurations
  ```python
  mqtt_client.connect(mqtt_host_name, port=mqtt_port, keepalive=60)
  ```

- JSON support
  ```python
  import json
  ```

- Publishing JSON message
  ```python
  payload = {
      'datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
      'temperature': s.temperature(),
      'humidity': s.humidity(),
      'staleness': s.staleness(),
      'bad_checksum': s.bad_checksum(),
      'short_message': s.short_message(),
      'missing_message': s.missing_message(),
      'sensor_resets': s.sensor_resets()
  }
  message_info = mqtt_client.publish(
     topic_to_publish, json.dumps(payload), qos=0)
  ```

You may have noticed that the host name has to be specified to the environment variable `MQTT_HOST_NAME`.

To get my AWS Message Broker name ([endpoint](https://docs.aws.amazon.com/cli/latest/reference/iot/describe-endpoint.html)), I ran the following command (`--profile kikuo-jp` is supplied to provide my credential),

```shell
aws iot --profile kikuo-jp describe-endpoint
```

And I got results similar to the following,

```json
{
    "endpointAddress": "XYZ.iot.ap-northeast-1.amazonaws.com"
}
```

I set the `MQTT_HOST_NAME` environment variable to `XYZ.iot.ap-northeast-1.amazonaws.com`.

```shell
export MQTT_HOST_NAME=XYZ.iot.ap-northeast-1.amazonaws.com
```

Then I ran [`src/DHT22_aws_iot.py`](src/DHT22_aws_iot.py)

```shell
python src/DHT22_aws_iot.py
```

### Subscribing messages from the AWS Message Broker

To subscribe messages from the AWS Message Broker, I just replaced certificates of the previous `mosquitto_sub` command with those for the AWS message broker (see below).

```shell
mosquitto_sub -h $MQTT_HOST_NAME -p 8883 -t 'home/temperature-and-humidity' --cafile root-ca.pem --cert mqtt-subscriber-1.pem.crt --key mqtt-subscriber-1.private.key
```

As I mentioned above, I had to allow the thing `home-monitor` the action `iot:Receive` in addition to the actions `iot:Connect` and `iot:Subscribe`.

### Subscribing messages via MQTT over WebSocket

I copied sample code from [here](https://docs.aws.amazon.com/iot/latest/developerguide/protocols.html), and saved them in [`docs/index.html`](docs/index.html) and [`docs/assets/js/SigV4Utils.js`](docs/assets/js/SigV4Utils.js).

I downloaded a custom AWS SDK for browser by taking the following steps,
1. Go to the [SDK page](https://aws.amazon.com/sdk-for-browser/)
2. Click on "Customize your SDK build"
3. Select only "AWS Iot"
4. Click on "Build"

I also downloaded [Eclipse Paho JavaScript Client](https://www.eclipse.org/paho/clients/js/).

Additionally, I downloaded the following libraries for presentation,
- [Vue.js](https://vuejs.org)
- [Bootstrap](http://getbootstrap.com)
- [jQuery](http://jquery.com)
- [Popper.js](https://popper.js.org) (required by Bootstrap but maybe unnecessary)

#### SecurityError on Safari

I got a `SecurityError` telling me "The operation is insecure" when Eclipse Paho accesses `localStorage` on Safari (Chrome was OK).

I followed a workaround suggested [here](https://forums.developer.apple.com/thread/87778), turning off the local file restriction of Safari, and I could avoid the error.
NOTE: I had to reload the page after turning off the local file restriction feature.

### GitHub Pages

The contents of [`docs`](docs) are now hosted at the [GitHub Pages](https://kikuomax.github.io/temperature-monitor/) (no MQTT endpoint and credentials are supplied but it should work with any AWS account).
