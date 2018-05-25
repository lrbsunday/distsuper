import logging

from peewee import DoesNotExist

from distsuper import CONFIG
from distsuper.common import tools, exceptions
from distsuper.models.models import Group, Machine, MachineGroup, Process


def create_or_update_machines(group, machines):
    machines = machines.strip().split(',')
    for machine_name in machines:
        try:
            machine = Machine.select() \
                .where(Machine.name == machine_name) \
                .get()
            machine.update_time = tools.get_now_time()
        except DoesNotExist:
            machine = Machine(name=machine_name)
        machine.save()
        create_or_update_machine_group(machine, group)


def create_or_update_group(group_name):
    try:
        group = Group.select() \
            .where(Group.name == group_name) \
            .get()
        group.update_time = tools.get_now_time()
    except DoesNotExist:
        group = Group(name=group_name)
    group.save()
    return group


def create_or_update_process(name, command,
                             status, touch_timeout, max_fail_count,
                             auto_start, auto_restart,
                             group_name):
    try:
        machines = Machine.select().join(MachineGroup).join(Group) \
            .where(Group.name == group_name)
    except DoesNotExist:
        raise exceptions.NoGroupException("机器组%s不存在" % group_name)

    machines = ','.join(machine.name for machine in machines)
    process = Process.update(command=command,
                             cstatus=status,
                             touch_timeout=touch_timeout,
                             max_fail_count=max_fail_count,
                             auto_start=auto_start,
                             auto_restart=auto_restart,
                             machines=machines,
                             update_time=tools.get_now_time()
                             ) \
        .where(Process.name == name)
    ret = process.execute()
    if ret == 0:
        process = Process(name=name,
                          command=command,
                          cstatus=status,
                          touch_timeout=touch_timeout,
                          max_fail_count=max_fail_count,
                          auto_start=auto_start,
                          auto_restart=auto_restart,
                          machines=machines)
        process.save()
    return process


def create_or_update_machine_group(machine, group):
    ret = MachineGroup.update(update_time=tools.get_now_time()
                              ) \
        .where(MachineGroup.machine == machine,
               MachineGroup.group == group) \
        .execute()
    if ret == 0:
        MachineGroup(machine=machine,
                     group=group).save()


def delete_expire_data(start_time):
    Process.delete().where(Process.update_time < start_time).execute()
    MachineGroup.delete().where(MachineGroup.update_time < start_time).execute()
    Machine.delete().where(Machine.update_time < start_time).execute()
    Group.delete().where(Group.update_time < start_time).execute()


def load_config():
    start_time = tools.get_now_time()

    for section_name in CONFIG.groups:
        group_name = section_name.split(':')[1]
        machines = CONFIG.config.get(section_name, 'machines')
        if not machines:
            logging.error("%s组的机器列表不能为空" % section_name)
        group = create_or_update_group(group_name)
        create_or_update_machines(group, machines)

    for section_name in CONFIG.programs:
        program_name = section_name.split(':')[1]
        command = CONFIG.config.get(section_name, 'command')
        if not command:
            logging.error("程序%s的启动命令不能为空" % section_name)
        auto_start = CONFIG.config.getboolean(section_name, 'auto_start',
                                              fallback=True)
        auto_restart = CONFIG.config.getboolean(section_name, 'auto_restart',
                                                fallback=True)
        group_name = CONFIG.config.get(section_name, 'group',
                                       fallback='')
        touch_timeout = CONFIG.config.getint(section_name, 'touch_timeout',
                                             fallback=10 * 365 * 24 * 3600)
        max_fail_count = CONFIG.config.getint(section_name, 'max_fail_count',
                                              fallback=3)
        create_or_update_process(program_name, command,
                                 int(auto_start), touch_timeout, max_fail_count,
                                 auto_start, auto_restart,
                                 group_name)

    delete_expire_data(start_time)
