#!/usr/bin/env python
# -*- mode: python; python-indent: 4; -*-


import argparse
import boto3
import logging


LOGGER = None


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    LOGGER = logging.getLogger(__name__)
    arg_parser = argparse.ArgumentParser(
        description='Downloads the certificate of an IoT device')
    arg_parser.add_argument(
        'certificate_id', metavar='ID', type=str,
        help='ID of the certificate to be obtained')
    arg_parser.add_argument(
        '--profile', metavar='PROFILE', type=str,
        help='optional profile name for the credential (default: None)')
    args = arg_parser.parse_args()
    LOGGER.info('certificate ID: %s', args.certificate_id)
    if args.profile:
        LOGGER.info('using profile: %s', args.profile)
        session = boto3.Session(profile_name=args.profile)
    else:
        session = boto3.Session()
    iot = session.client('iot')
    certificate = iot.describe_certificate(certificateId=args.certificate_id)
    print(certificate['certificateDescription']['certificatePem'])

