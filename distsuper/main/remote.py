import json
import logging

import requests

from distsuper.common import tools, exceptions


def remote_start(program_name, machine):
    url = "http://%s:3379/start" % machine
    try:
        response = requests.post(url, json={
            "program_name": program_name,
            "machine": machine
        }, timeout=3)
    except requests.ConnectionError:
        logging.error("接口请求失败: ConnectionError - %s" % url)
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
            r_dict.get("code"), r_dict.get("msg")))
        return False

    return True


def remote_stop(program_name, machine):
    url = "http://%s:3379/stop" % machine
    try:
        response = requests.post(url, json={
            "program_name": program_name
        }, timeout=3)
    except requests.ConnectionError:
        logging.error("接口请求失败: ConnectionError - %s" % url)
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
            r_dict.get("code"), r_dict.get("msg")))
        return False

    return True


def remote_status(program_name, machine):
    """

    :param program_name:
    :param machine:
    :return:
        True  运行中
        False 不存在
        None  未知
    """
    url = "http://%s:3379/status" % machine
    try:
        response = requests.post(url, json={
            "program_name": program_name
        }, timeout=3)
    except requests.ConnectionError:
        logging.error("接口请求失败: ConnectionError - %s" % url)
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
            r_dict.get("code"), r_dict.get("msg")))
        return None

    return r_dict['data']['status']


def remote_check(machine, status):
    if status == 'STARTING':
        ret = tools.retry(max_retry_count=3)(remote_check_only_once)(
            machine, status)
    elif status == 'STOPPING':
        ret = tools.retry()(remote_check_only_once)(
            machine, status)
    else:
        ret = None
    return ret


def remote_check_only_once(machine, status):
    url = "http://%s:3379/check" % machine
    try:
        response = requests.get(url, timeout=1)
    except requests.Timeout:
        raise exceptions.RetryException
    except requests.ConnectionError:
        if status == 'STOPPING':
            return False
        raise exceptions.RetryException

    if response.status_code != 200:
        return False

    return True
