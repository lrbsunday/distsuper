#!-*- encoding: utf-8 -*-
import logging

import requests

from distsuper.common import tools, exceptions

API_TIMEOUT = 20


def check_service_status(machine, port, status):
    if status == 'STARTING':
        ret = tools.retry(max_retry_count=3)(check_service_status_once)(
            machine, port, status)
    elif status == 'STOPPING':
        ret = tools.retry()(check_service_status_once)(
            machine, port, status)
    else:
        ret = None
    return ret


def check_service_status_once(machine, port, status):
    url = "http://%s:%s/check" % (machine, port)
    logging.info(url)
    try:
        response = requests.get(url, timeout=API_TIMEOUT)
    except requests.Timeout:
        raise exceptions.RetryException
    except requests.RequestException:
        if status == 'STOPPING':
            return False
        raise exceptions.RetryException

    if response.status_code != 200:
        return False

    return True
