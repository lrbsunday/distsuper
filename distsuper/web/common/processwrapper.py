#!-*- encoding: utf-8 -*-
import os
import sys
import time
import signal
import logging
import threading
import subprocess
from multiprocessing import Process

from distsuper.models.models import Process as ProcessModel
from distsuper.models import database


def default_signal_handler(process, info, *args):
    print('Received signal: ', args, info)
    process.terminate()


def register_signal_handler(sig, callback, default_callback=None):
    if callback and callable(callback):
        signal.signal(sig, callback)
    elif default_callback and callable(default_callback):
        signal.signal(sig, default_callback)


def handler_wrapper(process, info, signal_handler):
    if signal_handler is None:
        return None

    def __wrapper(*args):
        signal_handler(process, info, *args)

    return __wrapper


def register_signal_handlers(process, info, callbacks):
    """
    :param process: 子进程对象
    :param info: 附加信息，可以传递到handler
    :param callbacks: key => signal callback
        key可以取sighub、sigint、sigquit、sigterm、sigdefault
    :return:
    """
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


def touch_db(program_name, pid, touch_timeout):
    logging.info("进程%s运行中..." % program_name)
    timeout_timestamp = int(time.time() + touch_timeout)
    # noinspection PyBroadException
    try:
        ret = ProcessModel.update(timeout_timestamp=timeout_timestamp) \
            .where(ProcessModel.name == program_name,
                   ProcessModel.pid == pid) \
            .execute()
    except Exception:
        logging.exception("touch_db异常")
        return False
    if ret == 0:
        logging.warning("touch_db失败，没有这条记录，%s可能已停止" % program_name)
        return False
    return True


# noinspection PyBroadException
def task_wrapper(args, info, callbacks):
    try:
        database.close()
        info['pid'] = os.getpid()
        callbacks = callbacks or {}
        if 'sigdefault' not in callbacks:
            callbacks['sigdefault'] = default_signal_handler

        directory = info.get('directory')
        if directory is not None:
            os.chdir(directory)
        env = os.environ
        environment = info.get('environment')
        if environment is not None:
            environment = {
                field.strip().split('=', 2)[0].strip():
                    field.strip().split('=', 2)[1].strip()
                for field in environment.strip().split(';')
            }
            env.update(environment)

        stdout_logfile = info.get('stdout_logfile', '')
        stderr_logfile = info.get('stderr_logfile', '')
        stdout = sys.stdout
        stderr = sys.stderr
        if stdout_logfile:
            try:
                stdout = open(stdout_logfile, 'w+')
            except OSError:
                logging.warning("无法打开文件%s，日志打印到标准输出" % stdout_logfile)
        if stderr_logfile:
            try:
                stderr = open(stderr_logfile, 'w+')
            except OSError:
                logging.warning("无法打开文件%s，日志打印到标准错误" % stderr_logfile)

        process = subprocess.Popen(args, env=env, shell=True,
                                   stdout=stdout, stderr=stderr)
        register_signal_handlers(process, info, callbacks)

        def touch_db_loop(is_stop_info):
            running_time = 0  # 单位秒
            while 'stop' not in is_stop_info:
                time.sleep(1)
                if running_time <= 3:
                    running_time += 1
                if running_time == 3:
                    if 'start_success' in callbacks and callable(
                            callbacks['start_success']):
                        callbacks['start_success'](args, info)
                if running_time > 3:
                    if touch_db(info['program_name'], info['pid'],
                                info['touch_timeout']):
                        continue
                    else:
                        try:
                            process.terminate()
                        except OSError:
                            logging.warning("%s进程已停止" % info['program_name'])
                        break

        _is_stop_info = dict()
        thread = threading.Thread(target=touch_db_loop, args=(_is_stop_info,))
        thread.start()

        retcode = process.wait()
        _is_stop_info['stop'] = True
        if retcode == 0:
            if 'success' in callbacks and callable(
                    callbacks['success']):
                callbacks['success'](args, retcode, info)
        else:
            if 'fail' in callbacks and callable(
                    callbacks['fail']):
                callbacks['fail'](args, retcode, info)

        thread.join()
    except Exception:
        logging.exception('task wrapper')


def create_subprocess(args, info,
                      callbacks=None):
    p = Process(target=task_wrapper,
                args=(args, info, callbacks))
    p.start()
    return p


def success(args, *_):
    print('success', args)


def fail(args, *_):
    print('fail', args)


def sigint(args, *_):
    print('sigint', args)


if __name__ == '__main__':
    # print('create')
    # create_subprocess(['sleep', '1']).join()
    # print('create')
    # create_subprocess(['sleep', '1'], callbacks={'success': success}).join()
    # print('create')
    # create_subprocess(['sleep', '1'], callbacks={'fail': fail}).join()
    print('create')
    create_subprocess(['read_picture',
                       '--username=admin',
                       '--group=special',
                       '--channel=cctv2'],
                      '127.0.0.1',
                      callbacks={
                          'success': success,
                          'fail': fail,
                      }).join()
