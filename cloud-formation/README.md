# Using AWS CloudFormation to Build the Temperature Monitoring System

Here I am going to introduce [AWS CloudFormation](https://aws.amazon.com/cloudformation/) to build the same temperature monitoring system as described in [the top README](../README.md).

**Table of Contents**

<!-- TOC depthFrom:2 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 indent:ICAgIA== -->

- [Creating a certificate signing request (CSR) of a device](#creating-a-certificate-signing-request-csr-of-a-device)
- [Describing an AWS CloudFormation template for the temperature monitoring system](#describing-an-aws-cloudformation-template-for-the-temperature-monitoring-system)
    - [Defining a Thing representing a temperature sensor](#defining-a-thing-representing-a-temperature-sensor)
    - [Generating the certificate of the device](#generating-the-certificate-of-the-device)
    - [Attaching the certificate to the temperature sensor](#attaching-the-certificate-to-the-temperature-sensor)
    - [Declaring the policy of the temperature sensor](#declaring-the-policy-of-the-temperature-sensor)
    - [Attaching the policy to the certificate](#attaching-the-policy-to-the-certificate)
- [Deploying the AWS CloudFormation template](#deploying-the-aws-cloudformation-template)
- [Obtaining the certificate of the deployed device](#obtaining-the-certificate-of-the-deployed-device)
- [Installing certificates into the device](#installing-certificates-into-the-device)
- [Migrating to Amazon Trust Services (ATS) Endpoints](#migrating-to-amazon-trust-services-ats-endpoints)

<!-- /TOC -->

## Creating a certificate signing request (CSR) of a device

With AWS CloudFormation, a device certificate can be created as an [`AWS::IoT::Certificate`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iot-certificate.html) resource which requires a certificate signing request (CSR) as its input.
To issue a CSR, you need a private key of your device.
Because AWS CloudFormation has no feature to create a private key for a device, you have to create one by yourself.

Steps to create a private key have already been described in [the top README](README.md#signing-client-certificates).
Here are the steps,

1. Generate a private key for the temperature sensor.

    ```bash
    openssl genrsa -out private/mqtt-sensor-1.private.key 2048
    ```

2. Issue a CSR for the temperature sensor.

    ```bash
    openssl req -out cert/mqtt-sensor-1.csr -key private/mqtt-sensor-1.private.key -new
    ```

`cert/mqtt-sensor-1.csr` is going to be supplied to an [`AWS::IoT::Certificate`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iot-certificate.html) resource later.

## Describing an AWS CloudFormation template for the temperature monitoring system

[template.yaml](template.yaml) is the AWS CloudFormation template of our temperature monitoring system.
The following sections explain the contents of the template.

### Defining a Thing representing a temperature sensor

Define a Thing representing a temperature sensor with an [`AWS::IoT::Thing`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iot-thing.html) resource.

```yaml
TemperatureSensor1:
  Type: 'AWS::IoT::Thing'
  Properties:
    AttributePayload:
      Attributes:
        location: home
```

### Generating the certificate of the device

As described [above](#creating-a-certificate-signing-request-csr-of-a-device), we can issue a device certificate with an [`AWS::Iot::Certificate`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iot-certificate.html) resource.

```yaml
Resources:
  TemperatureSensor1Certificate:
    Type: 'AWS::IoT::Certificate'
    Properties:
      CertificateSigningRequest: !Ref TemperatureSensor1CSR
      Status: INACTIVE
```

The `CertificateSigningRequest` property should be the contents of the file `cert/mqtt-sensor-1.csr` generated in the section [Creating a certificate signing request (CSR) of a device](#creating-a-certificate-signing-request-csr-of-a-device).
As I did not want to embed the CSR in my template, I introduced the `TemperatureSensor1CSR` input parameter.
The CSR has to be specified to the `TemperatureSensor1CSR` input parameter, that can be done through the `--parameter-overrides` option of the [`aws cloudformation deploy`](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/deploy/index.html) command.

```bash
aws cloudformation deploy --template-file template.yaml --stack-name temperature-monitor --parameter-overrides "TemperatureSensor1CSR=`cat cert/mqtt-sensor-1.csr`"
```

### Attaching the certificate to the temperature sensor

An [`AWS::IoT::ThingPrincipalAttachment`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iot-thingprincipalattachment.html) resource attaches a certificate to a Thing.

```yaml
TemperatureSensor1ThingPrincipal:
  Type: 'AWS::IoT::ThingPrincipalAttachment'
  Properties:
    Principal: !GetAtt TemperatureSensor1Certificate.Arn
    ThingName: !Ref TemperatureSensor1
```

### Declaring the policy of the temperature sensor

An [`AWS::IoT::Policy`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iot-policy.html) resource declares a policy.

```yaml
TemperatureSensor1Policy:
  Type: 'AWS::IoT::Policy'
  Properties:
    PolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: 'Allow'
          Action:
            - 'iot:Connect'
          Resource:
            - !Sub 'arn:aws:iot:${AWS::Region}:${AWS::AccountId}:client/*'
        - Effect: 'Allow'
          Action:
            - 'iot:Publish'
          Resource:
            - !Sub 'arn:aws:iot:${AWS::Region}:${AWS::AccountId}:topic/home/temperature-and-humidity'
```

### Attaching the policy to the certificate

The policy has to be attached to the certificate with an [`AWS::IoT::PolicyPrincipalAttachment`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-iot-policyprincipalattachment.html) resource.

```yaml
TemperatureSensor1PolicyPrincipal:
  Type: 'AWS::IoT::PolicyPrincipalAttachment'
  Properties:
    Principal: !GetAtt TemperatureSensor1Certificate.Arn
    PolicyName: !Ref TemperatureSensor1Policy
```

## Deploying the AWS CloudFormation template

Use the [`aws cloudformation deploy`](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/deploy/index.html) command to deploy the AWS CloudFormation template.

```bash
aws cloudformation deploy --template-file template.yaml --stack-name temperature-monitor --parameter-overrides "TemperatureSensor1CSR=`cat cert/mqtt-sensor-1.csr`"
```

**NOTE:** You need a credential with sufficient privileges.

## Obtaining the certificate of the deployed device

The certificate of a device can be obtained with the [`aws iot describe-certificate`](https://docs.aws.amazon.com/cli/latest/reference/iot/delete-certificate.html) command which requires the ID of the certificate to be obtained.
The certificate ID is included in the ARN of the certificate of the deployed device, which is output as `TemperatureSensor1CertificateArn` when the stack is created.
The outputs of stacks can be obtained with the [`aws cloudformation describe-stacks`](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/describe-stacks.html) command.

```bash
aws --query $QUERY cloudformation describe-stacks --stack-name temperature-monitor
```

where `QUERY` is

```bash
QUERY=Stacks[?StackName==\'temperature-monitor\'].Outputs[]\|[?OutputKey==\'TemperatureSensor1CertificateArn\'].OutputValue\|[0]
```

See [JMESPath](http://jmespath.org) for more details about the query.

Then you will get an output similar to the following,

```
"arn:aws:iot:ap-northeast-1:123456789012:cert/6f10d091c691dc27b028218f6a53ed3ba598e0dcb0b27d6c9af1cc6c.."
```

The last part of the ARN `6f10d091c691dc27b028218f6a53ed3ba598e0dcb0b27d6c9af1cc6c..` is the certificate ID.

```bash
aws --query certificateDescription.certificatePem iot describe-certificate --certificate-id 6f10d091c691dc27b028218f6a53ed3ba598e0dcb0b27d6c9af1cc6c..
```

Then you will get the output similar to the following,

```
"-----BEGIN CERTIFICATE-----\nMIID0zCCArugAwIBAgIVAJ91y4xvzCv1oh/JPEGsluER7gJKMA0GCSqGSIb3DQEB\nCwUAME0xSzBJBgNVBAsMQkFtYXpvbiBXZWIgU2VydmljZXMgTz1BbWF6b24uY29t\nIEluYy4gTD1TZWF0dGxlIFNUPVdhc2hpbmd0b24gQz1VUzAeFw0xOTAyMTExNTU4\nMDBaFw00OTEyMzEyMzU5NTlaMIGWMQswCQYDVQQGEwJKUDERMA8GA1UECAwIS2Fu\nYWdhd2ExDzANBgNVBAcMBkF0c3VnaTEOMAwGA1UECgwFRW1vdG8xFDASBgNVBAsM\nC01RVFQgU2Vuc29yMRowGAYDVQQDDBFyYXNwYmVycnlwaS5sb2NhbDEhMB8GCSqG\nSIb3DQEJARYSa2lrdW9tYXhAZ21haWwuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOC\nAQ8AMIIBCgKCAQEA4IZBqRyXOTen8kT2cKzqPCx2xZSB6+AreXL7t5St5p3E3U4I\n..-----END CERTIFICATE-----\n"
```

The output is not very convenient, so I wrote a Python script [`scripts/download-certificate.py`](scripts/download-certificate.py) to download a certificate.

```bash
python scripts/download-certificate.py 6f10d091c691dc27b028218f6a53ed3ba598e0dcb0b27d6c9af1cc6c.. > cert/mqtt-sensor-1.pem
```

## Installing certificates into the device

By taking steps described above, you will have the following certificates,
- `cert/mqtt-sensor-1.pem`
- `private/mqtt-sensor-1.private.pem`

You can specify them to `mqtt_client.tls_set()` in [`DHT22_aws_iot.py`](../src/DHT22_aws_iot.py) as follows,
- `certfile` &leftarrow; `cert/mqtt-sensor-1.pem`
- `keyfile` &leftarrow; `private/mqtt-sensor-1.private.key`

## Migrating to Amazon Trust Services (ATS) Endpoints

According to [this page](https://docs.aws.amazon.com/iot/latest/developerguide/managing-device-certs.html), the Symantec CA which I previously used is now distrusted by many browsers.
So migration to new ATS endpoints is encouraged.

I am using an RSA 2048 bit key, so I chose the `Amazon Root CA 1`.
To obtain the new ATS endpoint, specify `iot:Data-ATS` to the `--endpoint-type` option of the [`aws iot describe-endpoint`](https://docs.aws.amazon.com/cli/latest/reference/iot/describe-endpoint.html) command.

```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS
```

You will get an output similar to the following,

```
{
    "endpointAddress": "abcdefghijklm-ats.iot.ap-northeast-1.amazonaws.com"
}
```

Specify it to the `MQTT_HOST_NAME` environment variable of the temperature sensor.

```bash
export MQTT_HOST_NAME=abcdefghijklm-ats.iot.ap-northeast-1.amazonaws.com
```
