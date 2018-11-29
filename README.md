# distsuper (v0.2.0)
仿照`supervisor`的功能实现的一个分布式进程监控工具，支持跨机器的进程失效转移。

![distsuper软件架构图][1]

## 安装
``` bash
pip install distsuper
```

## 启动
> 建议在初始化和启动服务之前，建立一工作路径，所有操作在该工作路径下进行。
> 用于保存配置文件、日志文件和程序执行中产生的临时文件。

### 启动服务端（1台机器）
``` bash
# 初始化配置文件，将在当前路径下生成一个默认的distsuper.ini文件
distsuperctl init config .
# 初始化数据库，将根据distsuper.ini配置的数据库，初始化数据库和表结构
distsuperctl init db
# 加载任务配置
distsuperctl load
# 启动服务端进程
distsuperd start
```
### 启动代理（n台机器）
``` bash
# 将服务器上的配置文件同步过来
...
# 在所有worker上启动客户端代理
distsuperagent start
```

### 验证
``` bash
# 若保留了默认配置中的测试任务，可以验证测试任务是否可以正常工作
distsuperctl start test # 启动test任务
distsuperctl status # 控制台输出会有一条名为test的任务在RUNNING
distsuperctl stop test # 停止test任务
```

## 组件
### 守护进程`distsuperd`
`distsuperd`是`distsuper`的核心组件之一，负责处理进程管理需求，包括：进程的启动、进程的停止、进程的失效转移。

``` bash
# 启动distsuperd服务
distsuperd start
```

### 管理工具`distsuperctl`
`distsuperctl`是`distsuper`的核心组件之一，通过该命令行工具用户可以初始化配置、数据库，加载配置更新，启动、停止进程，查询进程状态等。

``` bash
# 初始化配置文件，将在当前路径下生成一个默认的distsuper.ini文件
distsuperctl init config .
# 初始化数据库，将根据distsuper.ini配置的数据库，初始化数据库和表结构
distsuperctl init db
# 加载任务配置
distsuperctl load
# 状态查看
distsuperctl status
# 启动
distsuperctl start test
# 停止
distsuperctl stop test
```

### 机器代理`distsuperagent`
`distsuperagent`是`distsuper`的核心组件之一，是进程启动、进程停止和进程状态检查的实际执行模块，对`distsuperd`提供API接口，固定端口号3379。

``` bash
# 启动agent
distsuperagent start
# 停止agent
distsuperagent stop
# 重启agent
distsuperagent restart
```

## 失效转移
任何通过`distsuper`启动的进程会定期`touch_db()`，若超过`touch_timeout`没有收到`touch_db()`，`distsuperd`认为进程可能失效。经验证若确实失效，重启进程。

## 注意
* 如果distsuper安装在虚拟环境，请在`distsuper.ini`的`[http]`中指定`home=your virtualenv path`;
* 默认在当前路径下查找配置文件，若找不到在`/etc`下查找，若都不存在，命令无法执行；

    > `distsuperctl init config .`除外

* `distsuperagent`重启不会导致执行任务的重启，`distsuperctl`依然可以操作执行中的任务；

## API
### 模块导入
``` python
from distsuper.interface.api import create_process
from distsuper.interface.api import start_process
from distsuper.interface.api import stop_process
```

### create_process
``` python
def create_process(program_name, command,
                   auto_start=True, auto_restart=True,
                   machines='127.0.0.1', touch_timeout=5,
                   stdout_logfile='', stderr_logfile='',
                   max_fail_count=1):
    """ 创建一个进程，成功后接口立即返回，不等待进程启动
    :param program_name: 程序名称
    :param command: 执行的命令(shell script)
    :param auto_start: 是否自启动
    :param auto_restart: 是否自动重启
    :param machines: 可执行在哪些机器
    :param touch_timeout: 多长时间没有touch_db，认为超时
    :param stdout_logfile:
    :param stderr_logfile:
    :param max_fail_count: 多少次失败后不再重试
    :return:
        {"program_id": "xxxx:1234"}  - 程序唯一标识
        False - 进程创建失败
    """
```

### start_process
``` python
def start_process(program_id):
    """ 启动一个进程（只修改数据库状态），成功后接口立即返回，不等待进程真正启动
        后续进程的启动由distsuperd保证
        以后考虑增加状态回调功能
    :param program_id: 程序ID
    :return:
        True  - 进程启动成功
        False - 进程启动失败
        None  - 重复操作，忽略
    """
```

### stop_process
``` python
def stop_process(program_id):
    """ 停止一个进程（只修改数据库状态），成功后接口立即返回，不等待进程真正停止
        后续进程的停止由distsuperd保证
        以后考虑增加状态回调功能
    :param program_id: 程序ID
    :return:
        True  - 进程停止成功
        False - 进程停止失败
        None  - 重复操作，忽略
    """
```

### restart_process
``` python
def restart_process(program_id=None, program_name=None):
    """ 重启一个进程，直接调用agent接口去重启
    :param program_id: 程序ID
    :param program_name: 程序名称
    :return:
        True  - 进程重启成功
        False - 进程重启失败
        None  - 重复操作，忽略
    """
```

## Release Note

------
### v0.1.0
* distsuper的第一个版本，支持命令行操作

------
### v0.2.0
* distsuper的第二个版本，支持API操作

[1]: http://otl6ypoog.bkt.clouddn.com/Objectstoarge/images/2018-05-29/03680_5b0cbf43e4b009aef58c68cf.png?imageMogr2/auto-orient
