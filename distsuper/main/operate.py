#!-*- encoding: utf-8 -*-
import logging

from peewee import DoesNotExist, DatabaseError

from distsuper.common.constant import STATUS
from distsuper.models.models import Process
from distsuper.common import tools, exceptions

""" 进程状态(status)
参考supervisor的进程状态转换图
http://www.supervisord.org/_images/subprocess-transitions.png
0   STOPPED
10  STARTING 
20  RUNNING
40  STOPPING
100 EXITED
200 FATAL
-1  UNKNOWN

取消了BACKOFF状态，进程启动失败后变为STOPPED状态
autorestart只重启处于xx状态的进程
"""

logger = logging.getLogger("interface.server")


def change_status(program_id, from_status, to_status):
    """ 修改程序状态
    :param program_id: 程序ID
    :param from_status: 修改前的状态元组。程序状态不在from_status中时，修改失败
    :param to_status: 修改后的状态
    :return:
        True  - 修改成功
        False - 修改失败
    """
    if isinstance(from_status, int):
        from_status = (from_status,)

    fields = {
        "status": to_status,
        "update_time": tools.get_now_time()
    }
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        logger.error("程序%s不存在" % program_id)
        return False
    except DatabaseError:
        logger.exception("查询进程%s时，数据库发生异常" % program_id)
        return False

    if process.status not in from_status:
        logger.error("程序%s的状态%s不是%s" % (
            program_id, process.status, from_status))
        return False

    try:
        ret_code = Process.update(fields) \
            .where(Process.id == program_id,
                   Process.status << from_status).execute()
    except DatabaseError:
        logger.exception("程序%s的状态%s=>%s更新时，数据库发生异常" % (
            program_id, from_status, to_status))
        return False

    if ret_code == 0:
        logger.warning("程序%s的状态%s=>%s更新失败，ID或状态不匹配" % (
            program_id, from_status, to_status))
        return False

    return True


def get_program(program_id=None, program_name=None,
                status=None):
    """ 单条查询程序信息，program_id和program_name至少需要一个
    :param program_id: 程序ID
    :param program_name: 程序名称
    :param status: 程序状态
    :return: 程序对象
    """
    if program_id is not None and program_name is not None:
        raise exceptions.ParamValueException("program_id和program_name至少需要一个")

    conditions = []
    if program_id is not None:
        conditions.append(Process.id == program_id)
    if program_name is not None:
        conditions.append(Process.name == program_name)
    if status is not None:
        conditions.append(Process.status == status)

    try:
        program = Process.select().where(*conditions).get()
    except DoesNotExist:
        raise exceptions.ProgramNotExistInDB()
    except DatabaseError:
        logger.exception("查询程序%s时，数据库发生异常" % program_id)
        raise exceptions.MySQLDBException("查询程序时，数据库发生异常")

    return program


def get_programs(status=None):
    """ 批量查询程序信息
    :param status: 程序状态
    :return: 程序对象列表
    """
    conditions = []
    if status is not None:
        conditions.append(Process.status == status)

    try:
        if conditions:
            return Process.select().where(*conditions)
        else:
            return Process.select()
    except DatabaseError:
        logger.exception("查询程序列表时，数据库发生异常")
        raise exceptions.MySQLDBException("查询程序列表时，数据库发生异常")


def create_program(program_id, program_name, command, machines,
                   directory, environment,
                   auto_start, auto_restart, touch_timeout,
                   max_fail_count,
                   stdout_logfile, stderr_logfile):
    """ 添加一条程序
    :param program_id: UUID
    :param program_name:
    :param command:
    :param machines:
    :param directory:
    :param environment:
    :param auto_start:
    :param auto_restart:
    :param touch_timeout:
    :param max_fail_count:
    :param stdout_logfile:
    :param stderr_logfile:
    :return: 程序对象
    """
    try:
        fields = dict(id=program_id,
                      name=program_name,

                      command=command,
                      machines=machines,
                      directory=directory,
                      environment=environment,
                      auto_start=auto_start,
                      auto_restart=auto_restart,
                      touch_timeout=touch_timeout,
                      max_fail_count=max_fail_count,
                      stdout_logfile=stdout_logfile,
                      stderr_logfile=stderr_logfile,

                      machine="",
                      status=STATUS.STOPPED,
                      fail_count=0,
                      timeout_timestamp=0x7FFFFFFF
                      )
        program = Process.create(**fields)
        program.save()
        return program
    except DatabaseError:
        logger.exception("新增程序时，数据库发生异常")
        raise exceptions.MySQLDBException("新增程序时，数据库发生异常")


def update_program(program_id, **fields):
    """ 更新一条进程
    :param program_id:
    :return:
        True  - 更新成功
        False - 更新失败
    """
    try:
        Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        msg = "程序id=%s的配置不存在" % program_id
        logger.error(msg)
        raise exceptions.NoConfigException(msg)

    Process.update(**fields) \
        .where(Process.id == program_id) \
        .execute()
    return True
