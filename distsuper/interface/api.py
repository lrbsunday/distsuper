import logging
import json

import requests

from distsuper import CONFIG


def create_process(program_name, command,
                   auto_start=True, auto_restart=True,
                   machines='127.0.0.1', touch_timeout=5,
                   max_fail_count=1):
    """ 创建一个进程，成功后接口立即返回，不等待进程启动
    :param program_name: 程序名称
    :param command: 执行的命令(shell script)
    :param auto_start: 是否自启动
    :param auto_restart: 是否自动重启
    :param machines: 可执行在哪些机器
    :param touch_timeout: 多长时间没有touch_db，认为超时
    :param max_fail_count: 多少次失败后不再重试
    :return:
        True  - 进程创建成功
        False - 进程创建失败
    """
    url = "http://%s:%s/create" % (CONFIG.COMMON.server, CONFIG.SERVERHTTP.port)
    try:
        response = requests.post(url, json={
            "program_name": program_name,
            "command": command,
            "auto_start": auto_start,
            "auto_restart": auto_restart,
            "touch_timeout": touch_timeout,
            "machines": machines,
            "max_fail_count": max_fail_count,
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

    return r_dict["data"].get("program_id", "")


def start_process(program_id):
    """ 启动一个进程（只修改数据库状态），成功后接口立即返回，不等待进程真正启动
        后续进程的启动由distsuperd保证
        以后考虑增加状态回调功能
    :param program_id: 程序ID
    :return:
        True  - 进程启动成功
        False - 进程启动失败
        None  - 重复操作，忽略
    """
    url = "http://%s:%s/start" % (CONFIG.COMMON.server, CONFIG.SERVERHTTP.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id
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

    if "code" not in r_dict or r_dict["code"] not in (200, 515):
        logging.error("接口状态码异常：%s - %s" % (
            r_dict.get("code"), r_dict.get("msg")))
        return False

    if r_dict["code"] == 515:
        return None

    return True


def stop_process(program_id):
    """ 停止一个进程（只修改数据库状态），成功后接口立即返回，不等待进程真正停止
        后续进程的停止由distsuperd保证
        以后考虑增加状态回调功能
    :param program_id: 程序ID
    :return:
        True  - 进程停止成功
        False - 进程停止失败
        None  - 重复操作，忽略
    """
    url = "http://%s:%s/stop" % (CONFIG.COMMON.server, CONFIG.SERVERHTTP.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id
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

    if "code" not in r_dict or r_dict["code"] not in (200, 515):
        logging.error("接口状态码异常：%s - %s" % (
            r_dict.get("code"), r_dict.get("msg")))
        return False

    if r_dict["code"] == 515:
        return None

    return True