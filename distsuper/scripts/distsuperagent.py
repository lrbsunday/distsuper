import os
import subprocess
import logging
import sys

import click

from distsuper.scripts.common import check_config
from distsuper.main.remote import remote_check
from distsuper import CONFIG


@click.group()
def main():
    check_config()


@main.command()
def start():
    if os.path.exists(CONFIG.HTTP.pid_file_path):
        logging.warning("当前目录下存在pidfile，请确保agent没有启动，"
                        "并删除pidfile后再试")
        sys.exit(-1)
    args = 'uwsgi --ini {}:http'.format(CONFIG.config_file_path).split()
    ret = subprocess.Popen(args).wait()
    if ret == 0 and remote_check('127.0.0.1', 'STARTING'):
        logging.info("agent启动成功")
    else:
        logging.info("agent启动失败")


@main.command()
def stop():
    if not os.path.exists(CONFIG.HTTP.pid_file_path):
        logging.warning("找不到pidfile，请确保agent已启动，"
                        "并在pidfile所在路径下执行该命令")
        sys.exit(-1)
    args = 'uwsgi --stop {}'.format(CONFIG.HTTP.pid_file_path).split()
    ret = subprocess.Popen(args).wait()
    if ret == 0 and not remote_check('127.0.0.1', 'STOPPING'):
        logging.info("agent停止成功")
    else:
        logging.info("agent停止失败")


@main.command()
def restart():
    if not os.path.exists(CONFIG.HTTP.pid_file_path):
        logging.warning("找不到pidfile，请确保agent已启动，"
                        "并在pidfile所在路径下执行该命令")
        sys.exit(-1)
    args = 'uwsgi --reload {}'.format(CONFIG.HTTP.pid_file_path).split()
    ret = subprocess.Popen(args).wait()
    if ret == 0 and remote_check('127.0.0.1', 'STARTING'):
        logging.info("agent重启成功")
    else:
        logging.info("agent重启失败")


if __name__ == '__main__':
    main()
