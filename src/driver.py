from networking.sender import Sender
from networking.receiver import Receiver
from collections import defaultdict
from multiprocessing import Process, Value
from threading import Lock
from system_data.monitor import Monitor
from system_data.instance_data import InstanceData
from configparser import ConfigParser
import subprocess
import shlex
from typing import Optional
from utils.constants import *


NODES = defaultdict(int)


class Node:
    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        self.cpu_stable = True
        self.memory_stable = True
        self.all_node_status = defaultdict(lambda: None)
        self.all_node_status_lock = Lock()
        self.my_status = None
        self.my_status_lock = Lock()
        self.node_recv_progress = {node_ip: False for node_ip in NODES}
        self.node_recv_progress_lock = Lock()

    def update_my_status(self):
        while True:
            monitor = Monitor()
            monitor.monitor_proc.start()
            while not monitor.instance_data:
                pass
            self.my_status_lock.acquire()
            monitor.instance_data_lock.acquire()
            self.my_status = monitor.instance_data
            monitor.instance_data_lock.release()
            self.check_stability()
            self.my_status_lock.release()

    def check_stability(self):
        self.my_status_lock.acquire()
        if self.my_status.cpu_utilization > 90:
            self.cpu_stable = False
        elif self.my_status.memory_utilization > 90:
            self.memory_stable = False
        self.my_status_lock.release()

    def recv(self, sos: Value):
        while True:
            receiver = Receiver()
            data = receiver.receive()
            if sos.value == 1 and data.sos:
                sender = Sender(data.sender_ip, data.sender_port)
                self.my_status_lock.acquire()
                sender.send(data=self.my_status)
                self.my_status_lock.release()
                continue
            if not data.sos:
                self.all_node_status_lock.acquire()
                self.all_node_status[data.sender_ip] = (
                    data.get_cpu_utilization(),
                    data.get_memory_utilization(),
                    data.get_cpu(),
                    data.get_memory(),
                )
                self.all_node_status_lock.release()

                self.node_recv_progress_lock.acquire()
                self.node_recv_progress[data.sender_ip] = True
                if False in self.node_recv_progress:
                    self.node_recv_progress_lock.release()
                    continue
                sos.value = 1
                self.node_recv_progress = {node_ip: False for node_ip in NODES}
                self.node_recv_progress_lock.release()

    def get_target(self) -> str:
        threshold_factor = 1
        while True:
            if not self.cpu_stable:
                self.all_node_status_lock.acquire()
                self.my_status_lock.acquire()
                all_nodes_cpu_stats = {
                    node_ip: (cpu_utilization, total_cpu)
                    for node_ip, (
                        cpu_utilization,
                        _,
                        total_cpu,
                        _,
                    ) in self.all_node_status.items()
                    if cpu_utilization <= NODE_SELECTION_THRESHOLD_CPU_UTILIZATION
                    and total_cpu
                    >= (NODE_SELECTION_THRESHOLD / threshold_factor)
                    * self.my_status.get_cpu()
                }
                self.all_node_status_lock.release()
                self.my_status_lock.release()

                if not all_nodes_cpu_stats:
                    threshold_factor *= 2
                    continue

                min_viable = float("inf")
                min_viable_ip = None
                for node_ip, (_, total_cpu) in all_nodes_cpu_stats:
                    min_viable = min(min_viable, total_cpu)
                    min_viable_ip = node_ip

                return min_viable_ip

            if not self.memory_stable:
                self.all_node_status_lock.acquire()
                self.my_status_lock.acquire()
                all_nodes_memory_stats = {
                    node_ip: (memory_utilization, total_memory)
                    for node_ip, (
                        _,
                        memory_utilization,
                        _,
                        total_memory,
                    ) in self.all_node_status.items()
                    if memory_utilization <= NODE_SELECTION_THRESHOLD_MEMORY_UTILIZATION
                    and total_memory
                    >= (NODE_SELECTION_THRESHOLD / threshold_factor)
                    * self.my_status.get_memory()
                }
                self.all_node_status_lock.release()
                self.my_status_lock.release()

                if not all_nodes_memory_stats:
                    threshold_factor *= 2
                    continue

                min_viable = float("inf")
                min_viable_ip = None
                for node_ip, (_, total_memory) in all_nodes_memory_stats:
                    min_viable = min(min_viable, total_memory)
                    min_viable_ip = node_ip

                return min_viable_ip

    def migrate(
        self,
        checkpoint_name: str,
        container_name: str,
        pem_dir: str,
        checkpoint_dir: str,
        node_ip: str,
    ) -> tuple[Optional[str], bool]:
        ret = subprocess.call(
            shlex.split(
                "../migrate "
                + " ".join(
                    [checkpoint_name, container_name, pem_dir, checkpoint_dir, node_ip]
                )
            )
        )

        if ret == 1:
            print("Migration unsuccessful")
            return (None, False)

        return (ret, True)


config = ConfigParser()
config.read("config.ini")
node = Node(config["DEFAULT"]["IP"], config["DEFAULT"]["PORT"])

for section in config.sections():
    NODES[config[section]["IP"]] = config[section]["PORT"]


recv_sos = Value("i", 1)

receiver_process = Process(target=node.recv, args=(recv_sos,))
receiver_process.start()
status_update_process = Process(target=node.update_my_status)
status_update_process.start()

while True:
    while node.cpu_stable and node.memory_stable:
        pass

    recv_sos.value = 0

    for node_ip, node_port in NODES.items():
        sender = Sender(node_ip, node_port)
        sender.send(sos=True)

    while recv_sos.value == 0:
        pass

    candidate_target = node.get_target()
    checkpoint_name = node.migrate(
        candidate_target,
    )  # TODO
    if not node.cpu_stable:
        node.cpu_stable = True
    if not node.memory_stable:
        node.memory_stable = True
    checkpoint_name_sender = Sender(candidate_target, NODES[candidate_target])
    checkpoint_name_sender.send(data=InstanceData(misc_message=checkpoint_name))
