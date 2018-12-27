#!-*- encoding: utf-8 -*-
import os
import sys
import json
import time
import signal
import logging
import threading
import subprocess

from peewee import DoesNotExist

from distsuper.models.models import Process as ProcessModel
from distsuper.common import tools
from distsuper.common.constant import STATUS

logger = logging.getLogger("wrapper")


# noinspection PyUnusedLocal
def sigdefault(process, info, *args):
    program_id = info['program_id']
    logger.info("进程%s收到信号，即将退出" % program_id)
    os.killpg(process.pid, signal.SIGKILL)


# noinspection PyUnusedLocal
def sigterm(process, info, *args):
    program_id = info['program_id']
    logger.info("进程%s被SIG_TERM信号杀死" % program_id)
    os.killpg(process.pid, signal.SIGKILL)


# noinspection PyUnusedLocal
def fail(args, retcode, info):
    program_id = info['program_id']
    logger.info("进程%s执行失败" % program_id)


# noinspection PyUnusedLocal
def success(args, retcode, info):
    program_id = info['program_id']
    logger.info("进程%s执行成功" % program_id)


def register_signal_handlers(process, info, callbacks):
    """
    :param process: 子进程对象
    :param info: 附加信息，可以传递到handler
    :param callbacks: key => signal callback
        key可以取sighub、sigint、sigquit、sigterm、sigdefault
    :return:
    """

    def register_signal_handler(sig, callback, default_callback=None):
        if callback and callable(callback):
            signal.signal(sig, callback)
        elif default_callback and callable(default_callback):
            signal.signal(sig, default_callback)

    def handler_wrapper(_process, _info, signal_handler):
        if signal_handler is None:
            return None

        def __wrapper(*args):
            signal_handler(_process, _info, *args)

        return __wrapper

    defaultcallback = handler_wrapper(process, info,
                                      callbacks.get('sigdefault'))
    register_signal_handler(signal.SIGINT,
                            handler_wrapper(process, info,
                                            callbacks.get('sigint')),
                            default_callback=defaultcallback)
    register_signal_handler(signal.SIGQUIT,
                            handler_wrapper(process, info,
                                            callbacks.get('sigquit')),
                            default_callback=defaultcallback)
    register_signal_handler(signal.SIGTERM,
                            handler_wrapper(process, info,
                                            callbacks.get('sigterm')),
                            default_callback=defaultcallback)


def touch_db(program_id, touch_timeout):
    logger.info("进程%s运行中..." % program_id)
    timeout_timestamp = int(time.time() + touch_timeout)
    # 如果程序处于STARTING或STOPPING状态，无需touch db
    try:
        process = ProcessModel.select() \
            .where(ProcessModel.id == program_id) \
            .get()
    except DoesNotExist:
        logger.warning("touch_db失败，没有这条记录，%s可能已停止" % program_id)
        return False

    if process.status in (STATUS.STARTING, STATUS.STOPPING):
        return True

    # noinspection PyBroadException
    try:
        ret = ProcessModel.update(timeout_timestamp=timeout_timestamp) \
            .where(ProcessModel.id == program_id,
                   ProcessModel.status == STATUS.RUNNING) \
            .execute()
    except Exception:
        logger.exception("touch_db异常")
        return False

    if ret == 0:
        logger.warning("touch_db失败，没有这条记录，%s可能已停止" % program_id)
        return False

    return True


# noinspection PyBroadException
def task_wrapper(args, info):
    callbacks = {
        'on_success': success,
        'on_fail': fail,
        'sigdefault': sigdefault,
        'sigterm': sigterm
    }

    # 当前路径
    directory = info.get("directory")
    if directory is not None:
        os.chdir(directory)

    # 环境变量
    env = os.environ
    environment = info.get('environment')
    if environment is not None:
        environment = {
            field.strip().split('=', 2)[0].strip():
                field.strip().split('=', 2)[1].strip()
            for field in environment.strip().split(';')
        }
        env.update(environment)

    # 日志文件
    stdout_logfile = info.get('stdout_logfile', '')
    stderr_logfile = info.get('stderr_logfile', '')
    stdout = sys.stdout
    stderr = sys.stderr
    if stdout_logfile:
        tools.get_logger("wrapper",
                         file_name=stdout_logfile,
                         level=logging.INFO,
                         reset=True)
        try:
            stdout = open(stdout_logfile, 'a')
        except OSError:
            logger.warning("无法打开文件%s，日志打印到标准输出" % stdout_logfile)
    if stderr_logfile:
        try:
            stderr = open(stderr_logfile, 'a')
        except OSError:
            logger.warning("无法打开文件%s，日志打印到标准错误" % stderr_logfile)

    # 启动子进程
    logger.info("启动子进程")
    process = subprocess.Popen(args, env=env, shell=True,
                               stdout=stdout, stderr=stderr,
                               preexec_fn=os.setsid)

    # 注册回调函数
    register_signal_handlers(process, info, callbacks)

    # noinspection PyBroadException
    def touch_db_loop(_stop_info):
        while True:
            try:
                if _stop_info["stop"]:
                    break
                if not touch_db(info['program_id'], info['touch_timeout']):
                    p = _stop_info["process"]
                    logger.error("touch db失败，进程即将退出")
                    os.killpg(p.pid, signal.SIGKILL)
                    break
            except Exception:
                logger.exception("touch db发生未知异常")
            time.sleep(1)

    # touch db 线程
    stop_info = {
        "stop": False,
        "process": process
    }
    thread = threading.Thread(target=touch_db_loop, args=(stop_info,))
    thread.start()

    # 处理进程结束的状态码
    retcode = process.wait()
    stop_info["stop"] = True
    if retcode == 0:
        if 'on_success' in callbacks and \
                callable(callbacks['on_success']):
            callbacks['on_success'](args, retcode, info)
    else:
        if 'on_fail' in callbacks and \
                callable(callbacks['on_fail']):
            callbacks['on_fail'](args, retcode, info)

    thread.join()


def main():
    try:
        pid = os.fork()
    except OSError:
        sys.exit(1)

    if pid != 0:
        sys.exit(0)

    os.setsid()

    args = json.loads(sys.argv[1])
    info = json.loads(sys.argv[2])

    task_wrapper(args, info)
