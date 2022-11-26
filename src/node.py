from utils.const_and_glob import *
from system_data.monitor import Monitor
from networking.receiver import Receiver
from networking.sender import Sender
from typing import Optional, Tuple
import subprocess
import shlex
from multiprocessing.managers import BaseManager


class Node:
    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        self.cpu_stable = True
        self.memory_stable = True
        self.all_node_status = {node_ip: None for node_ip in NODES}
        self.my_status = None
        self.node_recv_progress = {node_ip: False for node_ip in NODES}

    def update_my_status(self):
        while True:
            monitor = Monitor()
            monitor.monitor_proc.start()
            while not monitor.instance_data:
                pass
            self.my_status = monitor.instance_data
            self.check_stability()

    def check_stability(self):
        if self.my_status.cpu_utilization > 90:
            self.cpu_stable = False
        elif self.my_status.memory_utilization > 90:
            self.memory_stable = False

    def recv(self, sos: int):
        while True:
            receiver = Receiver()
            data = receiver.receive()
            if sos.value == 1 and data.sos:
                sender = Sender(data.sender_ip, data.sender_port)
                my_status_copy = self.my_status.copy()
                sender.send(data=my_status_copy)
                continue
            if not data.sos:
                self.all_node_status[data.sender_ip] = (
                    data.get_cpu_utilization(),
                    data.get_memory_utilization(),
                    data.get_cpu(),
                    data.get_memory(),
                )

                self.node_recv_progress[data.sender_ip] = True
                if False in self.node_recv_progress:
                    continue
                sos.value = 1
                self.node_recv_progress = {node_ip: False for node_ip in NODES}

    def get_target(self) -> str:
        threshold_factor = 1
        while True:
            if not self.cpu_stable:
                all_node_status_copy = self.all_node_status.copy()
                all_nodes_cpu_stats = {
                    node_ip: (cpu_utilization, total_cpu)
                    for node_ip, (
                        cpu_utilization,
                        _,
                        total_cpu,
                        _,
                    ) in all_node_status_copy.items()
                    if cpu_utilization <= NODE_SELECTION_THRESHOLD_CPU_UTILIZATION
                    and total_cpu
                    >= (NODE_SELECTION_THRESHOLD / threshold_factor)
                    * self.my_status.get_cpu()
                }

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
                all_node_status_copy = self.all_node_status.copy()
                all_nodes_memory_stats = {
                    node_ip: (memory_utilization, total_memory)
                    for node_ip, (
                        _,
                        memory_utilization,
                        _,
                        total_memory,
                    ) in all_node_status_copy.items()
                    if memory_utilization <= NODE_SELECTION_THRESHOLD_MEMORY_UTILIZATION
                    and total_memory
                    >= (NODE_SELECTION_THRESHOLD / threshold_factor)
                    * self.my_status.get_memory()
                }

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
    ) -> Tuple[Optional[str], bool]:
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
