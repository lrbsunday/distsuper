#!-*- encoding: utf-8 -*-
import logging
import json

import requests

from distsuper import CONFIG

API_TIMEOUT = 30


def create_process(program_name, command,
                   directory=None, environment=None,
                   auto_start=True, auto_restart=True,
                   machines='127.0.0.1',
                   touch_timeout=5,
                   stdout_logfile='/dev/null', stderr_logfile='/dev/null',
                   max_fail_count=1):
    """ 创建进程
    :param program_name: 程序名称，不能重复
    :param command: 执行的命令(shell script)
    :param directory: 启动路径
    :param environment: 环境变量，多个分号分隔，如：A=a;B=b;C=c
    :param auto_start: 是否自启动
    :param auto_restart: 是否自动重启
    :param machines: 可执行在哪些机器，多个分号分隔，如：machines='127.0.0.1;localhost'
    :param touch_timeout: 多长时间没有touch_db，认为超时，单位秒
    :param stdout_logfile: 标准输出存储的日志文件
    :param stderr_logfile: 标准错误存储的日志文件
    :param max_fail_count: 超过多少次失败后不再重试
    :return:
        > 0  - dpid
        = 0  - 进程创建失败
    """
    url = "http://%s:%s/create" % (CONFIG.DISTSUPERCTL.host,
                                   CONFIG.DISTSUPERCTL.port)
    try:
        response = requests.post(url, json={
            "program_name": program_name,
            "command": command,
            "directory": directory,
            "environment": environment,
            "auto_start": auto_start,
            "auto_restart": auto_restart,
            "touch_timeout": touch_timeout,
            "machines": machines,
            "max_fail_count": max_fail_count,
            "stdout_logfile": stdout_logfile,
            "stderr_logfile": stderr_logfile
        }, timeout=API_TIMEOUT)
    except requests.RequestException:
        logging.error("server接口请求失败: RequestException - %s" % url)
        return 0

    if response.status_code != 200:
        logging.error("server接口请求失败: %s - %s" % (response.status_code, url))
        return 0

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("server接口返回结果解析失败 - %s" % response.text)
        return 0

    if "code" not in r_dict or r_dict["code"] != 200:
        logging.error("server接口状态码异常：%s - %s" % (
            r_dict.get("code", -1), r_dict.get("dmsg", "")))
        return 0

    return r_dict["data"]["program_id"]


def start_process(program_id=None, program_name=None):
    """ 启动进程
    :param program_id: 程序ID
    :param program_name: 程序名称
    :return:
        True  - 进程启动成功或已启动
        False - 进程启动失败
    """
    url = "http://%s:%s/start" % (CONFIG.DISTSUPERCTL.host,
                                  CONFIG.DISTSUPERCTL.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id,
            "program_name": program_name
        }, timeout=API_TIMEOUT)
    except requests.RequestException:
        logging.error("server接口请求失败: RequestException - %s" % url)
        return False

    if response.status_code != 200:
        logging.error("server接口请求失败: %s - %s" % (response.status_code, url))
        return False

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("server接口返回结果解析失败 - %s" % response.text)
        return False

    if "code" not in r_dict or r_dict["code"] != 200:
        logging.error("server接口状态码异常：%s - %s" % (
            r_dict.get("code", -1), r_dict.get("dmsg", "")))
        return False

    return True


def stop_process(program_id=None, program_name=None):
    """ 停止进程
    :param program_id: 程序ID
    :param program_name: 程序名称
    :return:
        True  - 进程停止成功或已停止
        False - 进程停止失败
    """
    url = "http://%s:%s/stop" % (CONFIG.DISTSUPERCTL.host,
                                 CONFIG.DISTSUPERCTL.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id,
            "program_name": program_name
        }, timeout=API_TIMEOUT)
    except requests.RequestException:
        logging.error("server接口请求失败: RequestException - %s" % url)
        return False

    if response.status_code != 200:
        logging.error("server接口请求失败: %s - %s" % (response.status_code, url))
        return False

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("server接口返回结果解析失败 - %s" % response.text)
        return False

    if "code" not in r_dict or r_dict["code"] != 200:
        logging.error("server接口状态码异常：%s - %s" % (
            r_dict.get("code", -1), r_dict.get("dmsg", "")))
        return False

    return True


def restart_process(program_id=None, program_name=None):
    """ 重启进程
    :param program_id: 程序ID
    :param program_name: 程序名称
    :return:
        True  - 进程重启成功
        False - 进程重启失败
    """
    url = "http://%s:%s/restart" % (CONFIG.DISTSUPERCTL.host,
                                    CONFIG.DISTSUPERCTL.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id,
            "program_name": program_name
        }, timeout=API_TIMEOUT)
    except requests.RequestException:
        logging.error("server接口请求失败: RequestException - %s" % url)
        return False

    if response.status_code != 200:
        logging.error("server接口请求失败: %s - %s" % (response.status_code, url))
        return False

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("server接口返回结果解析失败 - %s" % response.text)
        return False

    if "code" not in r_dict or r_dict["code"] != 200:
        logging.error("server接口状态码异常：%s - %s" % (
            r_dict.get("code", -1), r_dict.get("dmsg", "")))
        return False

    return True


def get_process(program_id=None, program_name=None):
    """ 查询进程
    :param program_id: 程序ID
    :param program_name: 程序名称
    :return: 进程信息字典，失败返回None
    """
    url = "http://%s:%s/status" % (CONFIG.DISTSUPERCTL.host,
                                   CONFIG.DISTSUPERCTL.port)
    try:
        response = requests.post(url, json={
            "program_id": program_id,
            "program_name": program_name
        }, timeout=API_TIMEOUT)
    except requests.RequestException:
        logging.error("server接口请求失败: RequestException - %s" % url)
        return None

    if response.status_code != 200:
        logging.error("server接口请求失败: %s - %s" % (response.status_code, url))
        return None

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("server接口返回结果解析失败 - %s" % response.text)
        return None

    if "code" not in r_dict or r_dict["code"] != 200:
        logging.error("server接口状态码异常：%s - %s" % (
            r_dict.get("code", -1), r_dict.get("dmsg", "")))
        return None

    return r_dict["data"]
