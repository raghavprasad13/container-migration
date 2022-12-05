from utils.const_and_glob import *
from system_data.instance_data import InstanceData
from multiprocessing.managers import BaseManager, NamespaceProxy
from networking.receiver import Receiver
from networking.sender import Sender
from typing import Optional, Tuple
import psutil
import os
import subprocess
import shlex
from configparser import ConfigParser


class NodeManager(BaseManager):
    pass


class NodeProxy(NamespaceProxy):
    _exposed_ = (
        "__getattribute__",
        "__setattr__",
        "__delattr__",
        "update_my_status",
        "recv",
        "get_target",
        "migrate",
    )

    def update_my_status(self):
        callmethod = object.__getattribute__(self, "_callmethod")
        return callmethod("update_my_status")

    def recv(self):
        callmethod = object.__getattribute__(self, "_callmethod")
        return callmethod("recv")

    def get_target(self):
        callmethod = object.__getattribute__(self, "_callmethod")
        return callmethod("get_target")

    def migrate(
        self,
        checkpoint_name: str,
        container_name: str,
        pem_dir: str,
        checkpoint_dir: str,
        node_ip: str,
    ):
        callmethod = object.__getattribute__(self, "_callmethod")
        return callmethod(
            "migrate",
            [checkpoint_name, container_name, pem_dir, checkpoint_dir, node_ip],
        )


class Node:
    def __init__(self, ip: str, port: int) -> None:
        config = ConfigParser()
        config.read("config.ini")
        self.ip = ip
        self.port = port
        self.cpu_stable = True
        self.memory_stable = True
        self.all_node_status = {node_ip: None for node_ip in NODES}
        self.my_status = None
        self.node_recv_progress = {node_ip: False for node_ip in NODES}
        self.container_name = config["DEFAULT"]["CONTAINER"]
        self.checkpoint_dir = config["DEFAULT"]["CHECKPOINT_DIR"]
        self.pem_dir = config["DEFAULT"]["PEM_DIR"]

    def update_my_status(self):
        while True:
            print("in update_my_status")
            self.monitor()
            self.check_stability()

    def monitor(self) -> None:
        print("in monitor")
        print()
        # cpu_percent = psutil.cpu_percent(5)
        # cpu_max_freq = psutil.cpu_freq().max
        # total_memory, used_memory, _ = map(
        #     int, os.popen("free -t -m").readlines()[-1].split()[1:]
        # )

        # instance_data = InstanceData(
        #     sender_ip_port=(self.ip, self.port),
        #     cpu_utilization=cpu_percent,
        #     memory_utilization=(used_memory / total_memory),
        #     cpu=cpu_max_freq,
        #     memory=total_memory,
        # )

        self.my_status = InstanceData(
            (self.ip, self.port), cpu_utilization=95, memory_utilization=50
        )
        print(f"monitor my_status: {self.my_status}")

    def check_stability(self):
        print("in check_stability")
        if self.my_status.cpu_utilization > 90:
            self.cpu_stable = False
        elif self.my_status.memory_utilization > 90:
            self.memory_stable = False

    def recv(self):
        while True:
            receiver = Receiver()
            data = receiver.receive()
            print("data received: {data}")
            if recv_sos.value == 1 and data.sos:
                print("in data.sos")
                sender = Sender(data.sender_ip, data.sender_port)
                my_status_copy = self.my_status.copy()
                sender.send(data=my_status_copy)
                continue
            if not data.sos:
                print("in not data.sos")
                self.all_node_status[data.sender_ip] = (
                    data.get_cpu_utilization(),
                    data.get_memory_utilization(),
                    data.get_cpu(),
                    data.get_memory(),
                )

                self.node_recv_progress[data.sender_ip] = True
                if False in self.node_recv_progress:
                    continue
                recv_sos.value = 1
                self.node_recv_progress = {node_ip: False for node_ip in NODES}

            if data.misc_message != None:
                pass  # TODO

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
                    if total_memory < min_viable:
                        min_viable = total_memory
                        min_viable_ip = node_ip

                return min_viable_ip

    def migrate(self) -> Tuple[Optional[str], bool]:
        checkpoint_name = "checkpoint_" + self.container_name
        ret = subprocess.call(
            shlex.split(
                "../migrate "
                + " ".join(
                    [
                        checkpoint_name,
                        self.container_name,
                        self.pem_dir,
                        self.checkpoint_dir,
                        self.ip,
                    ]
                )
            )
        )

        if ret == 1:
            print("Migration unsuccessful")
            return (None, False)

        return (ret, True)
