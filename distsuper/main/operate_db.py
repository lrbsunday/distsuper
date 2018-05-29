import logging

from peewee import DoesNotExist, IntegrityError

from distsuper.models.models import Process
from distsuper.common import tools, exceptions


def create_program(program_name, command, machines,
                   auto_start, auto_restart, touch_timeout,
                   max_fail_count, source):
    """ 创建program，直接返回，后续由distsuperd启动
        shell和api均可使用这个模式覆盖配置信息
        * 按program_name去重，重复的program将添加失败
    :param program_name:
    :param command:
    :param machines:
    :param auto_start:
    :param auto_restart:
    :param touch_timeout:
    :param max_fail_count:
    :param source:
    :return:
    """
    config_hash = tools.get_config_hash(command, machines,
                                        touch_timeout)

    try:
        program = Process.select().where(Process.name == program_name).get()
    except DoesNotExist:
        fields = dict(name=program_name,
                      command=command,
                      machines=machines,
                      auto_start=auto_start,
                      auto_restart=auto_restart,
                      touch_timeout=touch_timeout,
                      max_fail_count=max_fail_count,
                      cstatus=int(auto_start),
                      config_updated=0,
                      config_hash=config_hash,
                      source=source)
        program = Process(**fields)
        try:
            program.save()
            return "%s#%s" % (program.name, program.id)
        except IntegrityError:
            msg = "数据库完整性错误, 请稍后重试"
            logging.error(msg)
            raise exceptions.DBIntegrityException(msg)

    if program.source != source:
        msg = "不能操作其他来源的配置"
        logging.error(msg)
        raise exceptions.ParamValueException(msg)

    if program.pstatus in (0, 4, 5):
        fields = dict(machines=machines,
                      auto_start=auto_start,
                      auto_restart=auto_restart,
                      touch_timeout=touch_timeout,
                      max_fail_count=max_fail_count,
                      cstatus=int(auto_start),
                      pstatus=0,

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
                             auto_start, auto_restart, touch_timeout,
                             max_fail_count, source):
    """ 创建program，直接返回，后续由distsuperd启动
        只有shell才能使用这个模式覆盖配置信息
        * 按program_name去重，重复的program将添加失败
    :param program_name:
    :param command:
    :param machines:
    :param auto_start:
    :param auto_restart:
    :param touch_timeout:
    :param max_fail_count:
    :param source:
    :return:
    """
    try:
        return create_program(program_name, command, machines,
                              auto_start, auto_restart, touch_timeout,
                              max_fail_count, source)
    except exceptions.AlreadExistsException as e:
        config_hash = tools.get_config_hash(command, machines,
                                            touch_timeout)
        program = e.data['program']
        fields = dict(machines=machines,
                      auto_restart=auto_restart,
                      auto_start=auto_start,
                      touch_timeout=touch_timeout,
                      max_fail_count=max_fail_count,
                      cstatus=int(auto_start),

                      create_time=tools.get_now_time(),
                      update_time=tools.get_now_time())
        if program.config_hash != config_hash:
            fields['config_updated'] = 1
            fields['config_hash'] = config_hash
        ret_code = Process.update(**fields) \
            .where(Process.name == program_name,
                   Process.config_hash == program.config_hash) \
            .execute()
        if ret_code == 1:
            return "%s#%s" % (program.name, program.id)
        else:
            msg = "程序%s的状态冲突，请稍后再试" % program_name
            logging.error(msg)
            raise exceptions.DBConflictException(msg)


def start_program(program_id):
    """ 根据配置启动program，直接返回，后续由distsuperd启动
    :param program_id: name#id or id
    :return:
    """
    try:
        program = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        msg = "程序%s的配置不存在" % program_id
        logging.error(msg)
        raise exceptions.NoConfigException(msg)
    else:
        if program.pstatus in (1, 3):
            msg = "程序%s的状态目前无法启动，请稍后再试" % program_id
            logging.error(msg)
            raise exceptions.ProcessStatusException(msg)

        if program.pstatus in (2,):
            msg = "程序%s已启动，请不要重复操作" % program_id
            logging.error(msg)
            raise exceptions.DuplicateOperationException(msg)

        fields = dict(cstatus=1,
                      pstatus=0,
                      update_time=tools.get_now_time())
        ret_code = Process.update(**fields) \
            .where(Process.id == program_id,
                   Process.pstatus << [0, 4, 5]) \
            .execute()
        if ret_code == 1:
            pass
        else:
            msg = "程序%s的状态冲突，请稍后再试" % program_id
            logging.error(msg)
            raise exceptions.DBConflictException(msg)


def stop_program(program_id):
    try:
        process = Process.select().where(Process.id == program_id).get()
    except DoesNotExist:
        msg = "程序%s的配置不存在" % program_id
        logging.error(msg)
        raise exceptions.NoConfigException(msg)

    if process.pstatus in (1, 3):
        msg = "程序%s的状态目前无法停止，请稍后再试" % program_id
        logging.error(msg)
        raise exceptions.ProcessStatusException(msg)

    if process.pstatus in (0, 4, 5):
        msg = "程序%s已停止，请不要重复操作" % program_id
        logging.error(msg)
        raise exceptions.DuplicateOperationException(msg)

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