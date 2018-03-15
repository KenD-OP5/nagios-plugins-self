#! /usr/bin/env python

# Written for python 2.7
# This script is used for adding hosts, through line seperated json of host
# paramaters

# Stdlib imports
import argparse
import json
import logging

# 3rd party
import requests

# TODO: Capture signals to allow a smooth exit rather then crash.
# TODO: Read from stdin so data can be piped in.
# TODO: Add threading or multiprocessing so work can oe chunked.


def json_builder(template, host):
    data = template
    data["host_name"] = host
    return json.dumps(data)


def main():
    # TODO: Option to set logging level
    # Logging formatting options:
    #     https://docs.python.org/2/library/logging.html#logrecord-attributes
    log_entry_format = ':'.join(
        [
            '%(asctime)s',
            '%(levelname)s',
            '%(filename)s',
            '%(funcName)s',
            '%(lineno)s',
            '%(message)s',
        ]
    )

    logging.basicConfig(
        format=log_entry_format,
        level=logging.INFO,
        filename="hostloader.log"
    )
    logger = logging.getLogger('hostloader')

    ssl_check = True
    save_check = 0
    save_check_max = 20
    description = "Loads hosts into OP5 Monitor"

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "url",
        help="API URL of OP5 Monitor Install"
    )
    parser.add_argument(
        "user",
        help="Connection account"
    )
    parser.add_argument(
        "password",
        help="Account password"
    )
    parser.add_argument(
        "jsontemplate",
        help="File with JSON snippet"
    )
    parser.add_argument(
        "hostsfile",
        help="File with hosts to add"
    )
    parser.add_argument(
        "--nossl",
        action="store_true",
        help="Surpress SSL warnings"
    )
    parser.add_argument(
        "--upper",
        action="store_true",
        help="Set hostname to uppercase"
    )
    parser.add_argument(
        "--lower",
        action="store_true",
        help="Set hostname to lowercase"
    )
    args = parser.parse_args()

    logger.info("Passed Arguments: {}".format(args))

    if args.nossl:
        print("Surpressing SSL warnings...")
        ssl_check = False
        requests.packages.urllib3.disable_warnings()

    url = args.url
    user = args.user
    password = args.password
    case_upper = args.upper
    case_lower = args.lower

    config_host = '/'.join(
        [
            url,
            "api",
            "config",
            "host",
        ]
    )
    config_change = '/'.join(
        [
            url,
            "api",
            "config",
            "change"
        ]
    )

    if (case_upper and case_lower):
        logger.error("There can be only one case option.")
        return 10

    with open(args.jsontemplate, 'r') as json_file:
        json_template = json.load(json_file)

    logger.info("JSON Template: {}".format(json_template))

    with open(args.hostsfile, 'r') as importfile:
        for host in importfile:
            host = host.rstrip()  # Stripping newline character from host

            if case_lower:
                host = host.lower()
            elif case_upper:
                host = host.upper()

            logger.info("Adding host {}".format(host))

            json_payload = json_builder(json_template, host)

            # TODO: Move posts into generic post function.
            r = requests.post(
                config_host,
                data=json_payload,
                verify=ssl_check,
                auth=(user, password),
                headers={'content-type': 'application/json'}
            )

            logger.info('Header: {}'.format(r.headers))
            logger.info('Request: {}'.format(r.request))
            logger.info('Text: {}'.format(r.text))

            if save_check < save_check_max:
                save_check += 1
            else:
                logger.info("Saved")

                r = requests.post(
                    config_change,
                    data={},
                    verify=ssl_check,
                    auth=(user, password)
                )

                save_check = 0

            if 'str' in host:
                break

    return 0


if __name__ == '__main__':
    main()
