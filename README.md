# distsuper (v1.0.0)

仿照`supervisor`的功能实现的一个分布式进程监控工具。
* 支持跨机器进程的失效转移
* 支持命令行和API两种方式的进程管理
* 支持pip、docker、docker-compose方式部署


## 安装

### pip安装

#### 安装
``` bash
pip install distsuper
```

#### 启动服务（1台机器）
``` bash
# 初始化配置文件，将在当前路径下生成一个默认的distsuper.ini文件，根据需要适当修改配置文件
# 可以手动将配置文件移动到/etc/distsuper.ini
# 其他命令优先在当前路径下查找配置文件，若不存在，查找/etc。若仍然不存在，命令执行失败
distsuperctl init config .

# 初始化数据库，将根据distsuper.ini配置的数据库，初始化数据库和表结构
distsuperctl init db

# 启动服务端进程
distsuperd start

# 验证，输入如下命令后，若控制台输出程序列表（可能为空），表示服务正常启动
distsuperctl status
```

#### 启动代理（n台机器）
``` bash
# 初始化配置文件，将在当前路径下生成一个默认的distsuper.ini文件，根据需要适当修改配置文件
# 可以手动将配置文件移动到/etc/distsuper.ini
# 其他命令优先在当前路径下查找配置文件，若不存在，查找/etc。若仍然不存在，命令执行失败
distsuperctl init config .

# 在所有worker上启动客户端代理
distsuperagent start
```

### docker安装
略

### docker-compose安装
略


## 系统架构
![distsuper软件架构图][1]

### 守护进程`distsuperd`
`distsuperd`是`distsuper`的核心组件之一，负责处理进程管理需求，包括：进程的启动、进程的停止、进程的失效转移。

### 管理工具`distsuperctl`
`distsuperctl`是`distsuper`的核心组件之一，通过该命令行工具用户可以初始化配置、数据库，加载配置更新，启动、停止进程，查询进程状态等。

### 机器代理`distsuperagent`
`distsuperagent`是`distsuper`的核心组件之一，是进程启动、进程停止和进程状态检查的实际执行模块，对`distsuperd`提供API接口。

### 失效转移
任何通过`distsuper`启动的进程会定期`touch_db()`，若超过`touch_timeout`没有收到`touch_db()`，`distsuperd`认为进程可能失效。经验证若确实失效，重启进程。


## 命令行使用文档
``` bash
# 初始化配置文件，将在当前路径下生成一个默认的distsuper.ini文件
distsuperctl init config .
# 初始化数据库，将根据distsuper.ini配置的数据库，初始化数据库和表结构
distsuperctl init db
# 状态查看
distsuperctl status
# 启动
distsuperctl start <program_id>
# 停止
distsuperctl stop <program_id>
# 停止
distsuperctl restart <program_id>

# 启动agent
distsuperagent start
# 停止agent
distsuperagent stop
# 重启agent
distsuperagent restart

# 启动server
distsuperd start
# 停止server
distsuperd stop
# 重启server
distsuperd restart
```


## API使用文档

### 模块导入
``` python
from distsuper.api.server import *
```

### 创建进程
``` python
def create_process(program_name, command,
                   directory=None, environment=None,
                   auto_start=True,
                   machines='127.0.0.1',
                   stdout_logfile='/dev/null', stderr_logfile='/dev/null',
                   touch_timeout=5,
                   auto_restart=True, max_fail_count=1,
                   logger=default_logger):
    """ 创建进程
    :param program_name: 程序名称，不能重复
    :param command: 执行的命令(shell script)
    :param directory: 启动路径
    :param environment: 环境变量，多个分号分隔，如：A=a;B=b;C=c
    :param auto_start: 是否自启动 *******该字段已废弃*******
    :param machines: 可执行在哪些机器，多个分号分隔，如：machines='127.0.0.1;localhost'
    :param stdout_logfile: 标准输出存储的日志文件
    :param stderr_logfile: 标准错误存储的日志文件
    :param touch_timeout: 多长时间没有touch_db，认为超时，单位秒
    :param auto_restart: 是否自动重启
    :param max_fail_count: 超过多少次失败后不再重试
    :param logger: 日志对象
    :return:
        uuid  - 进程创建成功
        ""    - 进程创建失败
    """
```

### 启动进程
``` python
def start_process(program_id=None, program_name=None,
                  logger=default_logger):
    """ 启动进程
    :param program_id: 程序ID
    :param program_name: 程序名称
    :param logger: 日志对象
    :return:
        True  - 进程启动成功或已启动
        False - 进程启动失败
    """
```

### 停止进程
``` python
def stop_process(program_id=None, program_name=None,
                 logger=default_logger):
    """ 停止进程
    :param program_id: 程序ID
    :param program_name: 程序名称
    :param logger: 日志对象
    :return:
        True  - 进程停止成功或已停止
        False - 进程停止失败
    """
```

### 重启进程
``` python
def restart_process(program_id=None, program_name=None,
                    logger=default_logger):
    """ 重启进程
    :param program_id: 程序ID
    :param program_name: 程序名称
    :param logger: 日志对象
    :return:
        True  - 进程重启成功
        False - 进程重启失败
    """
```

### 查询进程状态
``` python
def get_process(program_id=None, program_name=None,
                logger=default_logger):
    """ 查询进程
    :param program_id: 程序ID
    :param program_name: 程序名称
    :param logger: 日志对象
    :return: 进程信息字典，失败返回None
    """
```


## 历史版本说明

### v0.1.0
* distsuper的第一个版本，支持命令行操作

### v0.2.0
* distsuper的第二个版本，支持API操作

### v1.0.0
* distsuper的正式版本，支持命令行、API管理进程
* 支持pip、docker、docker-compose方式部署
* 软件符合C-S架构、编码风格遵循pep8规范

[1]: http://otl6ypoog.bkt.clouddn.com/Objectstoarge/images/2018-05-29/03680_5b0cbf43e4b009aef58c68cf.png?imageMogr2/auto-orient
