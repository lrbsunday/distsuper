from distsuper.interface import api


class TestAPI(object):
    def test_api_by_id(self):
        dpid = api.create_process("test_api", "sleep 3600")  # 创建进程
        assert dpid != 0
        assert api.get_process(program_id=dpid)["status"] == 1

        assert api.stop_process(program_id=dpid)  # 正常停止
        assert api.get_process(program_id=dpid)["status"] == 0

        assert api.stop_process(program_id=dpid)  # 停止已停止的进程
        assert api.get_process(program_id=dpid)["status"] == 0

        assert api.restart_process(program_id=dpid)  # 重启已停止的进程
        assert api.get_process(program_id=dpid)["status"] == 1

        assert api.start_process(program_id=dpid)  # 启动已启动的进程
        assert api.get_process(program_id=dpid)["status"] == 1

        assert api.restart_process(program_id=dpid)  # 正常重启
        assert api.get_process(program_id=dpid)["status"] == 1

        assert api.stop_process(program_id=dpid)  # 正常停止
        assert api.get_process(program_id=dpid)["status"] == 0

        assert api.start_process(program_id=dpid)  # 正常启动
        assert api.get_process(program_id=dpid)["status"] == 1

        assert api.stop_process(program_id=dpid)  # 清理
        assert api.get_process(program_id=dpid)["status"] == 0

    def test_api_by_name(self):
        dpid = api.create_process("test_api", "sleep 3600")  # 创建进程
        assert dpid != 0
        process = api.get_process(program_id=dpid)
        assert api.stop_process(program_name=process.name)  # 正常停止
        assert api.stop_process(program_name=process.name)  # 停止已停止的进程
        assert api.restart_process(program_name=process.name)  # 重启已停止的进程
        assert api.start_process(program_name=process.name)  # 启动已启动的进程
        assert api.restart_process(program_name=process.name)  # 正常重启
        assert api.stop_process(program_name=process.name)  # 正常停止
        assert api.start_process(program_name=process.name)  # 正常启动
        assert api.stop_process(program_name=process.name)  # 清理

    def test_status(self):
        name = "test_api"
        command = "sleep 3600"
        directory = "/tmp"
        environment = "A=a;B=b;C=c"
        auto_start = False
        auto_restart = False
        machines = '127.0.0.1;localhost'
        touch_timeout = 60
        stdout_logfile = '/tmp/stdout.log'
        stderr_logfile = '/tmp/stderr.log'
        max_fail_count = 10
        dpid = api.create_process(name, command,
                                  directory=directory,
                                  environment=environment,
                                  auto_start=auto_start,
                                  auto_restart=auto_restart,
                                  machines=machines,
                                  touch_timeout=touch_timeout,
                                  stdout_logfile=stdout_logfile,
                                  stderr_logfile=stderr_logfile,
                                  max_fail_count=max_fail_count)
        process = api.get_process(program_id=dpid)
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
        assert api.stop_process(program_id=dpid)  # 清理
