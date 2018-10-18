#!-*- encoding: utf-8 -*-
import logging

from peewee import DoesNotExist, IntegrityError

from distsuper.models.models import Process
from distsuper.common import tools, exceptions


def create_program(program_name, command, machines,
                   directory, environment,
                   auto_start, auto_restart, touch_timeout,
                   max_fail_count, source,
                   stdout_logfile, stderr_logfile):
    """ 创建program，直接返回，后续由distsuperd启动
        shell和api均可使用这个模式覆盖配置信息
        * 按program_name去重，重复的program将添加失败
    :param program_name:
    :param command:
    :param machines:
    :param directory:
    :param environment:
    :param auto_start:
    :param auto_restart:
    :param touch_timeout:
    :param max_fail_count:
    :param source:
    :param stdout_logfile:
    :param stderr_logfile:
    :return:
    """
    config_hash = tools.get_config_hash(command, machines,
                                        touch_timeout)

    try:
        program = Process.select().where(Process.name == program_name).get()
    except DoesNotExist:
        fields = dict(name=program_name,
                      command=command,
                      directory=directory,
                      environment=environment,
                      machines=machines,
                      auto_start=auto_start,
                      auto_restart=auto_restart,
                      touch_timeout=touch_timeout,
                      max_fail_count=max_fail_count,
                      cstatus=int(auto_start),
                      config_updated=0,
                      config_hash=config_hash,
                      source=source,
                      stdout_logfile=stdout_logfile,
                      stderr_logfile=stderr_logfile,
                      )
        program = Process(**fields)
        try:
            program.save()
            return "%s#%s" % (program.name, program.id)
        except IntegrityError:
            msg = "数据库完整性错误, 请稍后重试"
            logging.exception(msg)
            raise exceptions.DBIntegrityException(msg)

    if program.source != source:
        msg = "不能操作其他来源的配置"
        logging.error(msg)
        raise exceptions.ParamValueException(msg)

    if program.pstatus in (0, 4, 5):
        fields = dict(command=command,
                      machines=machines,
                      directory=directory,
                      environment=environment,
                      auto_start=auto_start,
                      auto_restart=auto_restart,
                      touch_timeout=touch_timeout,
                      max_fail_count=max_fail_count,
                      cstatus=int(auto_start),
                      pstatus=0,
                      fail_count=0,
                      stdout_logfile=stdout_logfile,
                      stderr_logfile=stderr_logfile,

                      create_time=tools.get_now_time(),
                      update_time=tools.get_now_time())
        if program.config_hash != config_hash:
            fields['config_updated'] = 1
            fields['config_hash'] = config_hash
        ret_code = Process.update(**fields) \
            .where(Process.name == program_name,
                   Process.config_hash == program.config_hash,
                   Process.pstatus << [0, 4, 5]) \
            .execute()
        if ret_code == 1:
            return "%s#%s" % (program.name, program.id)
        else:
            msg = "程序%s的状态冲突，请稍后再试" % program_name
            logging.error(msg)
            raise exceptions.DBConflictException(msg)
    else:
        msg = "程序已存在, name=%s, machines=%s, command=%s" % (
            program_name, machines, command)
        logging.error(msg)
        raise exceptions.AlreadExistsException(msg, data={
            'program': program
        })


def create_or_update_program(program_name, command, machines,
                             directory, environment,
                             auto_start, auto_restart, touch_timeout,
                             max_fail_count, source,
                             stdout_logfile, stderr_logfile):
    """ 创建program，直接返回，后续由distsuperd启动
        只有shell才能使用这个模式覆盖配置信息
        * 按program_name去重，重复的program将添加失败
    :param program_name:
    :param command:
    :param machines:
    :param directory:
    :param environment:
    :param auto_start:
    :param auto_restart:
    :param touch_timeout:
    :param max_fail_count:
    :param source:
    :param stdout_logfile:
    :param stderr_logfile:
    :return:
    """
    try:
        return create_program(program_name, command, machines,
                              directory, environment,
                              auto_start, auto_restart, touch_timeout,
                              max_fail_count, source,
                              stdout_logfile, stderr_logfile)
    except exceptions.AlreadExistsException as e:
        config_hash = tools.get_config_hash(command, machines,
                                            touch_timeout)
        program = e.data['program']
        fields = dict(command=command,
                      machines=machines,
                      directory=directory,
                      environment=environment,
                      auto_restart=auto_restart,
                      auto_start=auto_start,
                      touch_timeout=touch_timeout,
                      max_fail_count=max_fail_count,
                      cstatus=int(auto_start),
                      pstatus=0,
                      fail_count=0,
                      source=source,
                      stdout_logfile=stdout_logfile,
                      stdoerr_logfile=stderr_logfile,

                      create_time=tools.get_now_time(),
                      update_time=tools.get_now_time())
        if program.config_hash != config_hash:
            fields['config_updated'] = 1
            fields['config_hash'] = config_hash
        ret_code = Process.update(**fields) \
            .where(Process.name == program_name,
                   Process.config_hash == program.config_hash,
                   Process.pstatus << [0, 4, 5]) \
            .execute()
        if ret_code == 1:
            return "%s#%s" % (program.name, program.id)
        else:
            msg = "程序%s的状态冲突，请稍后再试" % program_name
            logging.error(msg)
            raise exceptions.DBConflictException(msg)


def start_program(program_id=None, program_name=None):
    """ 根据配置启动program，直接返回，后续由distsuperd启动
    :param program_id: name#id or id
    :param program_name:
    :return:
    """
    try:
        logging.info("in start, program_id is %s, "
                     "program_name is %s" % (program_id, program_name))
        if program_id is not None:
            program = Process.select().where(Process.id == program_id).get()
        elif program_name is not None:
            program = Process.select().where(Process.name == program_name).get()
            program_id = program.id
        else:
            msg = "请求参数缺少program_id/program_name"
            logging.error(msg)
            raise exceptions.LackParamException(msg)
    except DoesNotExist:
        msg = "程序%s/%s的配置不存在" % (program_id, program_name)
        logging.error(msg)
        raise exceptions.NoConfigException(msg)
    else:
        if program.pstatus in (1, 3):
            msg = "程序%s的状态目前无法启动，请稍后再试" % program_id
            logging.error(msg)
            raise exceptions.ProcessStatusException(msg)

        if program.pstatus == 2 and program.cstatus == 1:
            msg = "程序%s已启动，请不要重复操作" % program_id
            logging.error(msg)
            raise exceptions.DuplicateOperationException(msg)

        if program.pstatus == 2 and program.cstatus == 0:
            fields = dict(cstatus=1,
                          update_time=tools.get_now_time())
            ret_code = Process.update(**fields) \
                .where(Process.id == program_id,
                       Process.pstatus == 2,
                       Process.cstatus == 0) \
                .execute()
            if ret_code == 1:
                return
            else:
                msg = "程序%s的状态冲突，请稍后再试" % program_id
                logging.error(msg)
                raise exceptions.DBConflictException(msg)

        fields = dict(cstatus=1,
                      pstatus=0,
                      fail_count=0,
                      update_time=tools.get_now_time())
        ret_code = Process.update(**fields) \
            .where(Process.id == program_id,
                   Process.pstatus << [0, 4, 5]) \
            .execute()
        if ret_code == 1:
            return
        else:
            msg = "程序%s的状态冲突，请稍后再试" % program_id
            logging.error(msg)
            raise exceptions.DBConflictException(msg)


def stop_program(program_id=None, program_name=None):
    """ 根据配置停止program，直接返回，后续由distsuperd启动
    :param program_id: name#id or id
    :param program_name:
    :return:
    """
    try:
        logging.info("in stop, program_id is %s, "
                     "program_name is %s" % (program_id, program_name))
        if program_id is not None:
            process = Process.select().where(Process.id == program_id).get()
        elif program_name is not None:
            process = Process.select().where(Process.name == program_name).get()
            program_id = process.id
        else:
            msg = "请求参数缺少program_id/program_name"
            logging.error(msg)
            raise exceptions.LackParamException(msg)
    except DoesNotExist:
        msg = "程序%s/%s的配置不存在" % (program_id, program_name)
        logging.error(msg)
        raise exceptions.NoConfigException(msg)

    if process.pstatus in (1, 3):
        msg = "程序%s的状态目前无法停止，请稍后再试" % program_id
        logging.error(msg)
        raise exceptions.ProcessStatusException(msg)

    if process.pstatus in (0, 4, 5) and process.cstatus == 0:
        msg = "程序%s已停止，请不要重复操作" % program_id
        logging.error(msg)
        raise exceptions.DuplicateOperationException(msg)

    if process.pstatus in (0, 4, 5) and process.cstatus == 1:
        fields = dict(cstatus=0,
                      update_time=tools.get_now_time())
        ret_code = Process.update(**fields) \
            .where(Process.id == program_id,
                   Process.pstatus << [0, 4, 5],
                   Process.cstatus == 1) \
            .execute()
        if ret_code == 1:
            return
        else:
            msg = "程序%s的状态冲突，请稍后再试" % program_id
            logging.error(msg)
            raise exceptions.DBConflictException(msg)

    fields = dict(cstatus=0,
                  update_time=tools.get_now_time())
    ret_code = Process.update(**fields) \
        .where(Process.id == program_id,
               Process.pstatus == 2) \
        .execute()
    if ret_code == 1:
        pass
    else:
        msg = "程序%s的状态冲突，请稍后再试" % program_id
        logging.error(msg)
        raise exceptions.DBConflictException(msg)
