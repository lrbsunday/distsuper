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
    """ 创建一个进程
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
        logging.error("接口请求失败: RequestException - %s" % url)
        return 0

    if response.status_code != 200:
        logging.error("接口请求失败: %s - %s" % (response.status_code, url))
        return 0

    try:
        r_dict = json.loads(response.text)
    except ValueError:
        logging.error("接口返回结果解析失败 - %s" % response.text)
        return 0

    if "code" not in r_dict or r_dict["code"] != 200:
        logging.error("接口状态码异常：%s - %s" % (
            r_dict["code"], r_dict["dmsg"]))
        return 0

    return r_dict["data"]["program_id"]


def start_process(program_id=None, program_name=None):
    """ 启动一个处于停止状态的进程
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

    if "code" not in r_dict or r_dict["code"] not in (200, 515):
        logging.error("接口状态码异常：%s - %s" % (
            r_dict["code"], r_dict["dmsg"]))
        return False

    return True


def stop_process(program_id=None, program_name=None):
    """ 停止一个进程（只修改数据库状态），成功后接口立即返回，不等待进程真正停止
        后续进程的停止由distsuperd保证
        以后考虑增加状态回调功能
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

    if "code" not in r_dict or r_dict["code"] not in (200, 515):
        logging.error("接口状态码异常：%s - %s" % (
            r_dict["code"], r_dict["dmsg"]))
        return False

    return True


def restart_process(program_id=None, program_name=None):
    """ 重启一个进程，直接调用agent接口去重启
    :param program_id: 程序ID
    :param program_name: 程序名称
    :return:
        True  - 进程重启成功
        False - 进程重启失败
    """
    return (stop_process(program_id=program_id, program_name=program_name)
            and start_process(program_id=program_id, program_name=program_name))


def get_process(program_id=None, program_name=None):
    """ 查询一个进程
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

    if "code" not in r_dict or r_dict["code"] not in (200, 515):
        logging.error("接口状态码异常：%s - %s" % (
            r_dict["code"], r_dict["dmsg"]))
        return None

    return r_dict["data"]
