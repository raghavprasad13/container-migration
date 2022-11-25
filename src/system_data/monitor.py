import psutil
from multiprocessing import Process
import os
import configparser
from instance_data import InstanceData
from threading import Lock


class Monitor:
    def __init__(self) -> None:
        self.monitor_proc = Process(target=self.monitor_cpu_mem)
        self.instance_data = None
        self.instance_data_lock = Lock()

    def monitor_cpu_mem(self) -> InstanceData:
        config = configparser.ConfigParser()
        config.read("../config.ini")
        my_ip = config["DEFAULT"]["IP"]
        my_port = config["DEFAULT"]["PORT"]
        cpu_percent = psutil.cpu_percent(5)
        cpu_max_freq = psutil.cpu_freq().max
        total_memory, used_memory, _ = map(
            int, os.popen("free -t -m").readlines()[-1].split()[1:]
        )

        instance_data = InstanceData(
            sender_ip_port=(my_ip, my_port),
            cpu_utilization=cpu_percent,
            memory_utilization=(used_memory / total_memory),
            cpu=cpu_max_freq,
            memory=total_memory,
        )

        self.instance_data_lock.acquire()
        self.instance_data = instance_data
        self.instance_data_lock.release()
