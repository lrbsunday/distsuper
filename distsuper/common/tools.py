#!-*- encoding: utf-8 -*-
import uuid
import os
import datetime
import logging
import time
import hashlib
import functools
import random
import threading
from multiprocessing.pool import ThreadPool
from traceback import format_exc as einfo

from .exceptions import *


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def get_now_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def time_it(module_name, logger=None, output_args=None, output_kwargs=None):
    if logger is None:
        logger = logging.getLogger('time_it')

    def decro(func):
        @functools.wraps(func)
        def wrapper(*arg, **kwargs):
            time1 = time.time()
            uuid_ = str(uuid.uuid4())
            if logger:
                output_msg = '[%s] %s.%s开始执行' % (
                    uuid_, module_name, func.__name__)
                if output_args:
                    for arg_index in output_args:
                        output_msg += ', 参数%s="%s"' % (
                            arg_index, arg[arg_index])
                if output_kwargs:
                    for arg_index in output_kwargs:
                        output_msg += ', 参数%s="%s"' % (
                            arg_index, arg[arg_index])
                logger.debug(output_msg)
            r = func(*arg, **kwargs)
            time2 = time.time()
            if logger:
                output_msg = '[%s] %s.%s结束执行，耗时%.2fs' % (
                    uuid_, module_name, func.__name__, time2 - time1)
                logger.debug(output_msg)
            return r

        return wrapper

    return decro


def get_logger(name, file_name, level=logging.INFO):
    """
    多次创建只有一份handlers
    支持root_logger和normal_logger的创建
    root_logger = tools.get_logger(None, 'package_log', level=logging.WARNING)
    normal_logger = tools.get_logger('interface', 'interface.log',
                                     level=logging.INFO)
    :param name:
    :param file_name:
    :param level:
    :return:
    """
    if name:
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger()
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s')

    if file_name:
        fh = logging.FileHandler(file_name)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        sh = logging.StreamHandler()
        sh.setLevel(level)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    return logger


def get_md5(s):
    return hashlib.md5(s.encode('utf8')).hexdigest().upper()


def deal_in_thread_pool(func, arg_list_list, t_num=4, to_random=False,
                        logger=logging):
    def __process(args):
        i, s = args[:2]
        args = args[2:]
        pid = os.getpid()
        tid = threading.current_thread().getName()
        args_str = json.dumps(args, ensure_ascii=False)
        logger.debug(
            "[%s][%s/%s][%s:%s] processing - %s" % (func.__name__, i, s,
                                                    pid, tid, args_str))
        start_time = time.time()
        try:
            ret = func(*args)
        except Exception as e:
            waste_time = round(time.time() - start_time, 2)
            logger.error("[%s][%s/%s][%s:%s][%ss] process failed: %s" % (
                func.__name__, i, s,
                pid, tid, waste_time, einfo()))
            raise e
        else:
            waste_time = round(time.time() - start_time, 2)
            logger.debug("[%s][%s/%s][%s:%s][%ss] process succeed" % (
                func.__name__, i, s,
                pid, tid, waste_time))
            return ret

    if to_random:
        random.shuffle(arg_list_list)

    total = len(list(arg_list_list))
    arg_list_list = [[i + 1, total] + arg_list for i, arg_list in
                     enumerate(arg_list_list)]
    logger.info('@@ deal %s %s tasks with %s threads pool' % (
        total, func.__name__, t_num))
    pool = ThreadPool(processes=t_num)
    results = pool.map(__process, arg_list_list, chunksize=1)
    logger.info('@@ all %s %s tasks done' % (total, func.__name__))
    return results


def retry(sleep_time=1, max_retry_count=None, logger=None):
    def __decro(func):
        @functools.wraps(func)
        def __wrapper(*args, **kwargs):
            retry_count = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except RetryException:
                    if max_retry_count is not None \
                            and retry_count >= max_retry_count:
                        return None
                    retry_count += 1
                    if logger:
                        logger.info("%s秒后重试%s..." % (sleep_time, func.__name__))
                    time.sleep(sleep_time)
                    continue

        return __wrapper

    return __decro


def loop_request():
    def __decro(func):
        @functools.wraps(func)
        def __wrapper(*args, **kwargs):
            offset = 0
            limit = 500
            total_results = []
            while True:
                results = func(*args, offset=offset, limit=limit, **kwargs)
                if not results:
                    break
                offset += limit
                total_results += results
            return total_results

        return __wrapper

    return __decro


def get_config_hash(command, machines, touch_timeout):
    return get_md5("#".join(
        map(str, [command, machines, touch_timeout])
    ))
