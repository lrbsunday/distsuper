import os
import time
import signal
import logging
import subprocess
from multiprocessing import Process

from distsuper.models.models import Process as ProcessModel
from distsuper.common import tools


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


def touch_db(program_name, touch_timeout):
    logging.info("进程%s运行中..." % program_name)
    timeout_timestamp = int(time.time() + touch_timeout)
    ret = ProcessModel.update(timeout_timestamp=timeout_timestamp,
                              update_time=tools.get_now_time()) \
        .where(ProcessModel.name == program_name) \
        .execute()
    if ret == 0:
        logging.warning("更新数据库失败，没有这条记录")
        return False
    return True


# noinspection PyBroadException
def task_wrapper(args, info, callbacks):
    try:
        info['pid'] = os.getpid()
        callbacks = callbacks or {}
        if 'sigdefault' not in callbacks:
            callbacks['sigdefault'] = default_signal_handler

        process = subprocess.Popen(args, shell=True)
        register_signal_handlers(process, info, callbacks)

        running_time = 0  # 单位秒
        while True:
            try:
                retcode = process.wait(1)
            except subprocess.TimeoutExpired:
                if running_time <= 3:
                    running_time += 1
                if running_time == 3:
                    if 'start_success' in callbacks and callable(
                            callbacks['start_success']):
                        callbacks['start_success'](args, info)
                touch_db(info['program_name'], info['touch_timeout'])
                continue

            if retcode == 0:
                if 'success' in callbacks and callable(callbacks['success']):
                    callbacks['success'](args, retcode, info)
            elif 'stop_flag' not in info:
                if 'fail' in callbacks and callable(callbacks['fail']):
                    callbacks['fail'](args, retcode, info)
            break
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
