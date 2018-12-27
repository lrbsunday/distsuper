class STATUS:
    STOPPED = 0
    STARTING = 10
    RUNNING = 20
    STOPPING = 40
    EXITED = 100
    FATAL = 200
    UNKNOWN = -1


def get_status_name(status):
    if status == STATUS.STOPPED:
        return "已停止"
    elif status == STATUS.STARTING:
        return "启动中"
    elif status == STATUS.RUNNING:
        return "运行中"
    elif status == STATUS.STOPPING:
        return "停止中"
    elif status == STATUS.EXITED:
        return "已退出"
    elif status == STATUS.FATAL:
        return "异常"
    else:
        return "未知"
