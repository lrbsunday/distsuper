# distsuper
仿照`supervisor`的功能实现的一个分布式进程监控工具，支持跨机器的进程失效转移

## 安装
``` bash
pip install distsuper
```
## 组件
### 守护进程`distsuperd`
`distsuperd`是`distsuper`的核心组件之一，负责处理进程管理需求，包括：进程的启动、进程的停止、进程的失效转移。

``` bash
# 启动distsuperd服务
distsuperd
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

## Release Note

------
### v0.1.0
* distsuper的第一个版本，支持命令行操作

------
### v0.1.1
* todo

