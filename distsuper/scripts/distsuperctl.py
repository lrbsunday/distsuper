import os
import logging

import click

from distsuper.scripts.common import check_config


@click.group()
def main():
    pass


@main.command()
@click.argument('process')
def start(process):
    from distsuper.main.shell import start_process_by_shell

    start_process_by_shell(process, wait=True)


@main.command()
@click.argument('process')
def stop(process):
    from distsuper.main.shell import stop_process_by_shell

    stop_process_by_shell(process, wait=True)


@main.command()
def status():
    from distsuper.main.shell import get_status_by_shell

    get_status_by_shell()


@main.command()
def load():
    from distsuper.main.load import load_config

    load_config()


@main.command()
@click.argument('obj',
                type=click.Choice(['db', 'config', 'all']))
@click.argument('path', default='./')
@click.option('--force', '-f', is_flag=True)
def init(obj, path, force=False):
    if obj == 'db':
        check_config()
        init_db()
    elif obj == 'config':
        init_config(force, path)


def init_config(force, path):
    orig_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  os.path.pardir,
                                  'configure', 'distsuper.ini')
    dest_file_path = '%s/distsuper.ini' % path
    if os.path.exists(dest_file_path) and not force:
        logging.warning('distsuper.ini已存在, 如需覆盖请使用-f/--force选项')
    else:
        os.system("cp -f %s %s" % (orig_file_path, dest_file_path))


def init_db():
    from distsuper import CONFIG
    from distsuper.models import create_database, drop_database
    drop_database(CONFIG.DB.db)
    create_database(CONFIG.DB.db)
    from distsuper.models import database
    from distsuper.models.models import Group, Machine, \
        MachineGroup, Process
    database.drop_tables([Group, Machine, MachineGroup, Process],
                         safe=True)
    database.create_tables([Group, Machine, MachineGroup, Process])


if __name__ == '__main__':
    main()
