#!-*- encoding: utf-8 -*-
import json
import logging

import requests

from distsuper import CONFIG
from distsuper.common import tools, exceptions

API_TIMEOUT = 20
default_logger = logging.getLogger("client.agent")


def start_process(program_id, machine, logger=default_logger):
    url = "http://%s:%s/start" % (machine, CONFIG.DISTSUPERAGENT.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id
        }, timeout=API_TIMEOUT)
    except requests.RequestException:
        logger.error("agent接口请求失败: RequestException - %s" % url)
        return None

    if response.status_code != 200:
        logger.error("agent接口请求失败: %s - %s" % (response.status_code, url))
        return None

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logger.error("agent接口返回结果解析失败 - %s" % response.text)
        return None

    if "code" not in r_dict:
        logger.error("agent接口返回结果格式不正确 - %s" % response.text)
        return False

    if r_dict["code"] != 200:
        logger.error("agent接口状态码异常：%s - %s" % (
            r_dict.get("code", -1), r_dict.get("dmsg", "")))
        return False

    return True


def stop_process(program_id, machine, logger=default_logger):
    url = "http://%s:%s/stop" % (machine, CONFIG.DISTSUPERAGENT.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id
        }, timeout=API_TIMEOUT)
    except requests.RequestException:
        logger.error("agent接口请求失败: RequestException - %s" % url)
        return None

    if response.status_code != 200:
        logger.error("agent接口请求失败: %s - %s" % (response.status_code, url))
        return None

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logger.error("agent接口返回结果解析失败 - %s" % response.text)
        return None

    if "code" not in r_dict:
        logger.error("agent接口返回结果格式不正确 - %s" % response.text)
        return False

    if r_dict["code"] != 200:
        logger.error("agent接口状态码异常：%s - %s" % (
            r_dict.get("code", -1), r_dict.get("dmsg", "")))
        return False

    return True


def _check_agent(machine, status):
    url = "http://%s:%s/check" % (machine, CONFIG.DISTSUPERAGENT.port)
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


def check_agent(status):
    machine = "127.0.0.1"
    if status == 'STARTING':
        ret = tools.retry(max_retry_count=3)(_check_agent)(machine, status)
    elif status == 'STOPPING':
        ret = tools.retry()(_check_agent)(machine, status)
    else:
        ret = None
    return ret
