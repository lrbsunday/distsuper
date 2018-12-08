from distsuper.interface import api


def test_create_api():
    api.create_process(
        "test_api", "export; echo stderr >&2; sleep 3600",
        directory="/Users/luanrongbo/",
        environment="env=env",
        auto_start=True,
        auto_restart=True,
        machines='127.0.0.1,localhost',
        touch_timeout=5,
        stdout_logfile='./stdout.log',
        stderr_logfile='./stderr.log',
        max_fail_count=2
    )


def test_start_api():
    pass


def test_restart_api():
    pass


def test_stop_api():
    pass
