#!-*- encoding: utf-8 -*-
import logging

from peewee import DoesNotExist, IntegrityError

from distsuper.models.models import Process
from distsuper.common import tools, exceptions


def get_program(program_id=None,
                program_name=None,
                status=None,
                lock=None):
    conditions = []
    if status is not None:
        conditions.append(Process.status == status)

    if lock is not None:
        conditions.append(Process.lock == lock)

    if program_id is not None:
        conditions.append(Process.id == program_id)

    if program_name is not None:
        conditions.append(Process.name == program_name)

    if program_id is not None and program_name is not None:
        try:
            program = Process.select().where(*conditions).get()
        except DoesNotExist:
            raise exceptions.ProgramNotExistInDB()
        return program
    else:
        return Process.select().where(*conditions)


def lock(program_id):
    # todo 如果已上锁，等待或重试
    if not Process.update(lock=1, lock_time=tools.get_now_time()) \
            .where(Process.id == program_id).execute():
        raise Exception("加锁失败")


def unlock(program_id):
    if Process.update(lock=0, lock_time=None) \
            .where(Process.id == program_id).execute():
        raise Exception("解锁失败")


def create_program(program_name, command, machines,
                   directory, environment,
                   auto_start, auto_restart, touch_timeout,
                   max_fail_count,
                   stdout_logfile, stderr_logfile):
    """ 在数据库中添加一条program
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
    :return:
    """
    try:
        program = Process.select().where(Process.name == program_name).get()
    except DoesNotExist:
        fields = dict(name=program_name,

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
                      pid=0,
                      status=0,
                      fail_count=0,
                      timeout_timestamp=0x7FFFFFFF
                      )
        program = Process(**fields)
        try:
            program.save()
            return program
        except IntegrityError:
            msg = "数据库完整性错误, 请稍后重试"
            logging.exception(msg)
            raise exceptions.DBIntegrityException(msg)

    if program.status == 0 and program.lock == 0:
        fields = dict(command=command,
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
                      pid=0,
                      status=0,
                      fail_count=0,
                      timeout_timestamp=0x7FFFFFFF,

                      create_time=tools.get_now_time(),
                      update_time=tools.get_now_time())
        ret_code = Process.update(**fields) \
            .where(Process.name == program_name) \
            .execute()
        if ret_code == 1:
            return program
        else:
            msg = "创建程序%s，更新数据库时发生异常" % program_name
            logging.error(msg)
            raise exceptions.DBConflictException(msg)
    else:
        msg = "程序%s运行中或被锁定，无法重新创建" % program_name
        logging.error(msg)
        raise exceptions.AlreadExistsException(msg, data={
            'program': program
        })


def start_program(machine, pid, program_id=None, program_name=None):
    """
    :param machine:
    :param pid:
    :param program_id:
    :param program_name:
    :return:
    """

    if program_id is not None:
        try:
            Process.select().where(Process.id == program_id).get()
        except DoesNotExist:
            msg = "程序id=%s的配置不存在" % program_id
            logging.error(msg)
            raise exceptions.NoConfigException(msg)

        fields = dict(status=1,
                      update_time=tools.get_now_time(),

                      machine=machine,
                      pid=pid,
                      fail_count=0,
                      timeout_timestamp=0x7fffffff)
        ret_code = Process.update(**fields) \
            .where(Process.id == program_id,
                   Process.status == 0) \
            .execute()
    elif program_name is not None:
        try:
            Process.select().where(Process.name == program_name).get()
        except DoesNotExist:
            msg = "程序name=%s的配置不存在" % program_name
            logging.error(msg)
            raise exceptions.NoConfigException(msg)

        fields = dict(status=1,
                      update_time=tools.get_now_time(),

                      machine=machine,
                      pid=pid,
                      fail_count=0,
                      timeout_timestamp=0x7fffffff)
        ret_code = Process.update(**fields) \
            .where(Process.name == program_name,
                   Process.status == 0) \
            .execute()
    else:
        msg = "请求参数缺少program_id/program_name"
        logging.error(msg)
        raise exceptions.LackParamException(msg)

    if ret_code:
        return True
    else:
        logging.error("程序%s/%s没有处于停止状态" % (program_id, program_name))
        return False


def stop_program(program_id=None, program_name=None):
    """
    :param program_id:
    :param program_name:
    :return:
    """
    if program_id is not None:
        try:
            Process.select().where(Process.id == program_id).get()
        except DoesNotExist:
            msg = "程序id=%s的配置不存在" % program_id
            logging.error(msg)
            raise exceptions.NoConfigException(msg)

        fields = dict(status=0,
                      update_time=tools.get_now_time())
        ret_code = Process.update(**fields) \
            .where(Process.id == program_id,
                   Process.status == 1) \
            .execute()
    elif program_name is not None:
        try:
            Process.select().where(Process.name == program_name).get()
        except DoesNotExist:
            msg = "程序name=%s的配置不存在" % program_name
            logging.error(msg)
            raise exceptions.NoConfigException(msg)

        fields = dict(status=0,
                      update_time=tools.get_now_time())
        ret_code = Process.update(**fields) \
            .where(Process.name == program_name,
                   Process.status == 1) \
            .execute()
    else:
        msg = "请求参数program_id和program_name至少存在一个"
        logging.error(msg)
        raise exceptions.LackParamException(msg)

    if ret_code:
        return True
    else:
        logging.error("程序%s/%s没有处于运行状态" % (program_id, program_name))
        return False
