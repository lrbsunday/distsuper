import os
import logging

from distsuper.api import server
from distsuper.scripts.distsuperctl import init_db
from distsuper.common.constant import STATUS

logging.getLogger().setLevel(logging.FATAL)
tmp_for_test = os.path.join(os.getcwd(), "tmp_for_test")
os.system("rm -rf %s" % tmp_for_test)
os.system("mkdir -p %s" % tmp_for_test)
init_db(True)


class TestAPI(object):
    def test_api_by_id(self):
        dpid = server.create_process("test_api_by_id", "sleep 60")  # 创建进程
        assert dpid
        assert server.get_process(program_id=dpid)["status"] == STATUS.RUNNING

        assert server.stop_process(program_id=dpid)  # 正常停止
        assert server.get_process(program_id=dpid)["status"] == STATUS.STOPPED

        assert server.stop_process(program_id=dpid)  # 停止已停止的进程
        assert server.get_process(program_id=dpid)["status"] == STATUS.STOPPED

        assert server.restart_process(program_id=dpid)  # 重启已停止的进程
        assert server.get_process(program_id=dpid)["status"] == STATUS.RUNNING

        assert server.start_process(program_id=dpid)  # 启动已启动的进程
        assert server.get_process(program_id=dpid)["status"] == STATUS.RUNNING

        assert server.restart_process(program_id=dpid)  # 正常重启
        assert server.get_process(program_id=dpid)["status"] == STATUS.RUNNING

        assert server.stop_process(program_id=dpid)  # 正常停止
        assert server.get_process(program_id=dpid)["status"] == STATUS.STOPPED

        assert server.start_process(program_id=dpid)  # 正常启动
        assert server.get_process(program_id=dpid)["status"] == STATUS.RUNNING

        assert server.stop_process(program_id=dpid)  # 清理
        assert server.get_process(program_id=dpid)["status"] == STATUS.STOPPED

    def test_server_by_name(self):
        dpid = server.create_process("test_server_by_name",
                                     "sleep 60")  # 创建进程
        assert dpid
        process = server.get_process(program_id=dpid)
        assert server.get_process(program_id=dpid)["status"] == STATUS.RUNNING

        assert server.stop_process(program_name=process["name"])  # 正常停止
        assert server.get_process(program_id=dpid)["status"] == STATUS.STOPPED

        assert server.stop_process(program_name=process["name"])  # 停止已停止的进程
        assert server.get_process(program_id=dpid)["status"] == STATUS.STOPPED

        assert server.restart_process(program_name=process["name"])  # 重启已停止的进程
        assert server.get_process(program_id=dpid)["status"] == STATUS.RUNNING

        assert server.start_process(program_name=process["name"])  # 启动已启动的进程
        assert server.get_process(program_id=dpid)["status"] == STATUS.RUNNING

        assert server.restart_process(program_name=process["name"])  # 正常重启
        assert server.get_process(program_id=dpid)["status"] == STATUS.RUNNING

        assert server.stop_process(program_name=process["name"])  # 正常停止
        assert server.get_process(program_id=dpid)["status"] == STATUS.STOPPED

        assert server.start_process(program_name=process["name"])  # 正常启动
        assert server.get_process(program_id=dpid)["status"] == STATUS.RUNNING

        assert server.stop_process(program_name=process["name"])  # 清理
        assert server.get_process(program_id=dpid)["status"] == STATUS.STOPPED

    def test_create_twice(self):
        dpid = server.create_process("test_create_twice",
                                     "sleep 60",
                                     auto_start=False)  # 创建进程
        assert dpid
        dpid = server.create_process("test_create_twice",
                                     "sleep 60")  # 创建进程
        assert dpid
        assert server.stop_process(program_id=dpid)  # 清理

    def test_status(self):
        name = "test_status"
        command = "sleep 60"
        directory = "/tmp"
        environment = "A=a;B=b;C=c"
        auto_start = False
        auto_restart = True
        machines = '127.0.0.1;localhost'
        touch_timeout = 60
        stdout_logfile = '/tmp/stdout.log'
        stderr_logfile = '/tmp/stderr.log'
        max_fail_count = 10
        dpid = server.create_process(name, command,
                                     directory=directory,
                                     environment=environment,
                                     auto_start=auto_start,
                                     auto_restart=auto_restart,
                                     machines=machines,
                                     touch_timeout=touch_timeout,
                                     stdout_logfile=stdout_logfile,
                                     stderr_logfile=stderr_logfile,
                                     max_fail_count=max_fail_count)
        assert dpid
        process = server.get_process(program_id=dpid)
        assert process["id"] == dpid
        assert process["name"] == name
        assert process["command"] == command
        assert process["directory"] == directory
        assert process["environment"] == environment
        assert process["auto_start"] == auto_start
        assert process["auto_restart"] == auto_restart
        assert process["machines"] == machines
        assert process["touch_timeout"] == touch_timeout
        assert process["stdout_logfile"] == stdout_logfile
        assert process["stderr_logfile"] == stderr_logfile
        assert process["max_fail_count"] == max_fail_count
        assert server.stop_process(program_id=dpid)  # 清理

    def test_directory(self):
        name = "test_directory"
        command = "test `pwd` = %s && sleep 60" % tmp_for_test
        dpid = server.create_process(name, command,
                                     directory=tmp_for_test,
                                     stdout_logfile="test_directory.log",
                                     stderr_logfile="test_directory.log")
        assert dpid
        assert server.stop_process(program_id=dpid)  # 清理

    def test_environment(self):
        name = "test_environment"
        environment = "AAA=aaa; BBB = bbb"
        command = "test $AAA = aaa && test $BBB = bbb && sleep 60"
        dpid = server.create_process(name, command,
                                     directory=tmp_for_test,
                                     environment=environment,
                                     stdout_logfile="test_environment.log",
                                     stderr_logfile="test_environment.log")
        assert dpid
        assert server.stop_process(program_id=dpid)  # 清理

    def test_logfile(self):
        name = "test_logfile"
        command = "echo stdout && echo stderr 1>&2 && sleep 60"
        dpid = server.create_process(name, command,
                                     directory=tmp_for_test,
                                     stdout_logfile="test_logfile_stdout.log",
                                     stderr_logfile="test_logfile_stderr.log")
        assert dpid
        assert server.stop_process(program_id=dpid)  # 清理

        with open(os.path.join(tmp_for_test, "test_logfile_stdout.log"),
                  encoding="utf-8") as fp:
            for line in fp:
                if line.strip() == "stdout":
                    break
            else:
                assert False
        with open(os.path.join(tmp_for_test, "test_logfile_stderr.log"),
                  encoding="utf-8") as fp:
            for line in fp:
                if line.strip() == "stderr":
                    break
            else:
                assert False

    def test_machines(self):
        name = "test_machines"
        command = "sleep 60"
        machines = "localhost;127.0.0.1"
        dpid = server.create_process(name, command,
                                     directory=tmp_for_test,
                                     machines=machines,
                                     stdout_logfile="test_machines.log",
                                     stderr_logfile="test_machines.log")
        assert dpid
        assert server.stop_process(program_id=dpid)  # 清理

        name = "test_machines"
        command = "sleep 60"
        machines = "wrong_machine"
        dpid = server.create_process(name, command,
                                     directory=tmp_for_test,
                                     machines=machines,
                                     stdout_logfile="test_machines.log",
                                     stderr_logfile="test_machines.log")
        assert dpid == ""

    def test_auto_start(self):
        name = "test_auto_start"
        command = "sleep 60"
        dpid = server.create_process(name, command,
                                     auto_start=False,
                                     directory=tmp_for_test,
                                     stdout_logfile="test_auto_start.log",
                                     stderr_logfile="test_auto_start.log")
        assert dpid
        assert server.get_process(program_id=dpid)["status"] == STATUS.STOPPED

    def test_auto_restart(self):
        pass

    def test_touch_timeout(self):
        pass

    def test_max_fail_count(self):
        pass
