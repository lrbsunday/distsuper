#!-*- encoding: utf-8 -*-
import os
import sys
import logging

import click

from distsuper.scripts.common import check_config
from distsuper.common import tools
from distsuper.common.constant import get_status_name
from distsuper.api import server as sa

"""
distsuperctl start {id}
distsuperctl stop {id}
distsuperctl restart {id}
distsuperctl status
distsuperctl init db [--drop]  # 初始化数据库
distsuperctl init config  # 初始化配置文件
"""


@click.group()
def main():
    pass


@main.command()
@click.argument('program_id')
def start(program_id):
    if sa.start_process(program_id=program_id):
        logging.info("进程启动成功")
    else:
        logging.error("进程启动失败")


@main.command()
@click.argument('program_id')
def stop(program_id):
    if sa.stop_process(program_id=program_id):
        logging.info("进程停止成功")
    else:
        logging.error("进程停止失败")


@main.command()
@click.argument('program_id')
def restart(program_id):
    if sa.restart_process(program_id=program_id):
        logging.info("进程重启成功")
    else:
        logging.error("进程重启失败")


@main.command()
def status():
    processes = sa.get_process()
    if processes is None:
        logging.error("获取进程信息失败")
        return

    titles = ["ID", "名称", "状态", "机器", "创建时间", "命令"]
    results = [titles]
    for process in processes:
        name = process["name"]
        _status = get_status_name(process["status"])
        machine = process["machine"] or "-"
        start_time = process["create_time"] or "-"
        command = process["command"] or "-"

        results.append([str(process["id"]), name, str(_status),
                        machine, start_time, command])

    if results:
        width_list = []
        for i in range(len(titles)):
            max_length = max(tools.char_length(result[i]) for result in results)
            width_list.append(max_length)

        for result in results:
            print('    '.join(["%-{}s".format(width
                                              - tools.unicode_count(field))
                               % field
                               for field, width in
                               zip(result, width_list)]))


@main.command()
@click.argument('obj',
                type=click.Choice(['db', 'config', 'all']))
@click.argument('path', default='.')
@click.option('--force', '-f', is_flag=True)
@click.option('--drop', '-d', is_flag=True)
def init(obj, path, force=False, drop=False):
    if obj == 'db':
        check_config()
        init_db(drop)
    elif obj == 'config':
        init_config(force, path)


def init_config(force, path):
    orig_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  os.path.pardir,
                                  'configure', 'distsuper.ini')
    dest_file_path = '%s/distsuper.ini' % path
    if os.path.exists(dest_file_path) and not force:
        logging.warning('distsuper.ini已存在, 如需覆盖请使用-f/--force选项')
        sys.exit(-1)
    else:
        os.system("cp -f %s %s" % (orig_file_path, dest_file_path))


def init_db(drop):
    from distsuper import CONFIG
    from distsuper.models import create_database, drop_database, database
    from distsuper.models.models import Process

    if drop:
        drop_database(CONFIG.DATABASE.db)

    create_database(CONFIG.DATABASE.db)
    database.create_tables([Process])


if __name__ == '__main__':
    main()
