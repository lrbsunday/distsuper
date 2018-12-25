#!-*- encoding: utf-8 -*-
import logging
import json

import requests

from distsuper import CONFIG

API_TIMEOUT = 20


def start_process(program_id, machine):
    url = "http://%s:%s/start" % (machine, CONFIG.DISTSUPERAGENT.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id
        }, timeout=API_TIMEOUT)
    except requests.RequestException:
        logging.error("agent接口请求失败: RequestException - %s" % url)
        return None

    if response.status_code != 200:
        logging.error("agent接口请求失败: %s - %s" % (response.status_code, url))
        return None

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("agent接口返回结果解析失败 - %s" % response.text)
        return None

    if "code" not in r_dict:
        logging.error("agent接口返回结果格式不正确 - %s" % response.text)
        return False

    if r_dict["code"] != 200:
        logging.error("agent接口状态码异常：%s - %s" % (
            r_dict.get("code", -1), r_dict.get("dmsg", "")))
        return False

    return r_dict["data"]["pid"]


def stop_process(program_id, machine):
    url = "http://%s:%s/stop" % (machine, CONFIG.DISTSUPERAGENT.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id
        }, timeout=API_TIMEOUT)
    except requests.RequestException:
        logging.error("agent接口请求失败: RequestException - %s" % url)
        return None

    if response.status_code != 200:
        logging.error("agent接口请求失败: %s - %s" % (response.status_code, url))
        return None

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("agent接口返回结果解析失败 - %s" % response.text)
        return None

    if "code" not in r_dict:
        logging.error("agent接口返回结果格式不正确 - %s" % response.text)
        return False

    if r_dict["code"] != 200:
        logging.error("agent接口状态码异常：%s - %s" % (
            r_dict.get("code", -1), r_dict.get("dmsg", "")))
        return False

    return True


def check_process_status(program_id, machine, pid):
    """
    :param program_id:
    :param machine:
    :param pid:
    :return:
        True  运行中
        False 不存在
        None  未知
    """
    url = "http://%s:%s/status" % (machine, CONFIG.DISTSUPERAGENT.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id,
            "pid": pid
        }, timeout=API_TIMEOUT)
    except requests.RequestException:
        logging.error("agent接口请求失败: RequestException - %s" % url)
        return None

    if response.status_code != 200:
        logging.error("agent接口请求失败: %s - %s" % (response.status_code, url))
        return None

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("agent接口返回结果解析失败 - %s" % response.text)
        return None

    if "code" not in r_dict:
        logging.error("agent接口返回结果格式不正确 - %s" % response.text)
        return False

    if r_dict["code"] != 200:
        logging.error("agent接口状态码异常：%s - %s" % (
            r_dict.get("code", -1), r_dict.get("dmsg", "")))
        return None

    return r_dict['data']['status']
