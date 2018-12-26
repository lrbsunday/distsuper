#!-*- encoding: utf-8 -*-
from peewee import *
from . import BaseModel


class Process(BaseModel):
    class Meta:
        table_name = "process"

    # 配置信息
    name = CharField(max_length=128, unique=True,
                     help_text="进程名称")
    command = TextField(help_text="启动命令")
    directory = CharField(max_length=256, null=True,
                          help_text="启动路径")
    environment = CharField(max_length=256, null=True,
                            help_text="环境变量")
    machines = CharField(max_length=256,
                         help_text="失效转移的机器列表")
    auto_start = BooleanField(default=True,
                              help_text="是否自动启动")
    auto_restart = BooleanField(default=True,
                                help_text="是否自动重启")
    stdout_logfile = CharField(max_length=256,
                               default='',
                               help_text="标准输出文件")
    stderr_logfile = CharField(max_length=256,
                               default='',
                               help_text="标准错误文件")
    touch_timeout = IntegerField(default=10 * 365 * 24 * 3600,
                                 help_text="进程保活时间")
    max_fail_count = IntegerField(default=3, null=True,
                                  help_text="默认最大失败次数，失败第4次时将不会重试")

    # 运行状态
    status = IntegerField(default=1,
                          help_text="0 停止中, 1 运行中")
    machine = CharField(max_length=256,
                        help_text="实际执行程序的机器")
    fail_count = IntegerField(default=0,
                              help_text="当前失败次数")
    timeout_timestamp = IntegerField(default=0x7FFFFFFF,
                                     help_text="超时时间")
