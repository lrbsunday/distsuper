from peewee import *
from . import BaseModel


class Group(BaseModel):
    """ 机器组 """

    class Meta:
        db_table = "group"

    name = CharField(max_length=128, unique=True)  # 机器组名称
    status = IntegerField(default=1)  # 在线状态，1 在线 0 不在线


class Machine(BaseModel):
    """ 机器列表 """

    class Meta:
        db_table = "machine"

    name = CharField(max_length=128, unique=True)  # 机器的名称或IP地址
    status = IntegerField(default=1)  # 在线状态，1 在线 0 不在线


class MachineGroup(BaseModel):
    """ 机器组 """

    class Meta:
        db_table = "machine_group"

    machine = ForeignKeyField(Machine)
    group = ForeignKeyField(Group)
    weight = IntegerField(default=1)  # 暂未使用


class Process(BaseModel):
    """ 进程配置
    status: 0 - 已停止
            1 - 启动中
            2 - 运行中
            3 - 停止中
            4 - 失败
            5 - 成功
    """

    class Meta:
        db_table = "process"

    name = CharField(max_length=128, unique=True)  # 进程名称
    cstatus = IntegerField(default=1)  # 0 不启动, 1 可启动

    command = CharField(max_length=1024)  # 启动命令
    machines = CharField(max_length=128)  # 失效转移的机器列表，空表示任意机器
    auto_start = BooleanField(default=True)  # 是否自动启动
    auto_restart = BooleanField(default=True)  # 是否自动重启
    touch_timeout = IntegerField(default=10 * 365 * 24 * 3600)
    max_fail_count = IntegerField(default=3)  # 默认失败次数

    machine = CharField(max_length=128, default='')  # 运行在哪台机器上machine
    pid = IntegerField(default=0)  # 进程ID
    pstatus = IntegerField(default=0)  # 运行状态

    fail_count = IntegerField(default=0)  # 失败次数
    timeout_timestamp = IntegerField(default=0x7FFFFFFF)
