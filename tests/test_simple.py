import os
import logging

from distsuper.api import server
from distsuper.scripts.distsuperctl import init_db

logging.getLogger().setLevel(logging.FATAL)
tmp_for_test = os.path.join(os.getcwd(), "tmp_for_test")
os.system("rm -rf %s" % tmp_for_test)
os.system("mkdir -p %s" % tmp_for_test)
init_db(True)


class TestAPI(object):
    def test_run(self):
        name = "test_run"
        command = "sleep 60"
        machines = "distsuperagent"
        dpid = server.create_process(name, command,
                                     directory=tmp_for_test,
                                     machines=machines,
                                     stdout_logfile="test_machines.log",
                                     stderr_logfile="test_machines.log")
        assert dpid
