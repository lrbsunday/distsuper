#!-*- encoding: utf-8 -*-
import json
import logging

import requests

from distsuper.common import tools, exceptions
from distsuper import CONFIG


def remote_start(program_id, machine):
    url = "http://%s:%s/start" % (machine, CONFIG.AGENTHTTP.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id,
            "machine": machine
        }, timeout=10)
    except requests.RequestException:
        logging.error("接口请求失败: RequestException - %s" % url)
        return False

    if response.status_code != 200:
        logging.error("接口请求失败: %s - %s" % (response.status_code, url))
        return False

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("接口返回结果解析失败 - %s" % response.text)
        return False

    if "code" not in r_dict or r_dict["code"] != 200:
        logging.error("接口状态码异常：%s - %s" % (
            r_dict.get("code"), r_dict.get("dmsg")))
        return False

    return True


def remote_stop(program_id, machine):
    url = "http://%s:%s/stop" % (machine, CONFIG.AGENTHTTP.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id
        }, timeout=10)
    except requests.RequestException:
        logging.error("接口请求失败: RequestException - %s" % url)
        return False

    if response.status_code != 200:
        logging.error("接口请求失败: %s - %s" % (response.status_code, url))
        return False

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("接口返回结果解析失败 - %s" % response.text)
        return False

    if "code" not in r_dict or r_dict["code"] != 200:
        logging.error("接口状态码异常：%s - %s" % (
            r_dict.get("code"), r_dict.get("dmsg")))
        return False

    return True


def remote_restart(program_id, machine):
    url = "http://%s:%s/restart" % (machine, CONFIG.AGENTHTTP.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id
        }, timeout=10)
    except requests.RequestException:
        logging.error("接口请求失败: RequestException - %s" % url)
        return False

    if response.status_code != 200:
        logging.error("接口请求失败: %s - %s" % (response.status_code, url))
        return False

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("接口返回结果解析失败 - %s" % response.text)
        return False

    if "code" not in r_dict or r_dict["code"] != 200:
        logging.error("接口状态码异常：%s - %s" % (
            r_dict.get("code"), r_dict.get("dmsg")))
        return False

    return True


def remote_status(program_id, machine):
    """
    :param program_id:
    :param machine:
    :return:
        True  运行中
        False 不存在
        None  未知
    """
    url = "http://%s:%s/status" % (machine, CONFIG.AGENTHTTP.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id
        }, timeout=10)
    except requests.RequestException:
        logging.error("接口请求失败: RequestException - %s" % url)
        return None

    if response.status_code != 200:
        logging.error("接口请求失败: %s - %s" % (response.status_code, url))
        return None

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("接口返回结果解析失败 - %s" % response.text)
        return None

    if "code" not in r_dict or r_dict["code"] != 200:
        logging.error("接口状态码异常：%s - %s" % (
            r_dict.get("code"), r_dict.get("dmsg")))
        return None

    return r_dict['data']['status']


def remote_check(machine, port, status):
    if status == 'STARTING':
        ret = tools.retry(max_retry_count=3)(remote_check_only_once)(
            machine, port, status)
    elif status == 'STOPPING':
        ret = tools.retry()(remote_check_only_once)(
            machine, port, status)
    else:
        ret = None
    return ret


def remote_check_only_once(machine, port, status):
    url = "http://%s:%s/check" % (machine, port)
    logging.info(url)
    try:
        response = requests.get(url, timeout=1)
    except requests.Timeout:
        raise exceptions.RetryException
    except requests.RequestException:
        if status == 'STOPPING':
            return False
        raise exceptions.RetryException

    if response.status_code != 200:
        return False

    return True
