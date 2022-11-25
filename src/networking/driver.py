from sender import Sender
from receiver import Receiver
from collections import defaultdict
from multiprocessing import Process, Value
from threading import Lock
from system_data.monitor import Monitor
from system_data.instance_data import InstanceData
import configparser
import subprocess
import shlex
from typing import Optional


NODES = {}


class Node:
    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        self.instance_stable = True
        self.all_node_status = defaultdict(lambda: None)
        self.all_node_status_lock = Lock()
        self.my_status = None
        self.my_status_lock = Lock()
        self.node_recv_progress = {node_ip: False for node_ip in NODES}
        self.node_recv_progress_lock = Lock()

    def update_my_status(self):
        monitor = Monitor()
        monitor.monitor_proc.start()
        while not monitor.instance_data:
            pass
        self.my_status_lock.acquire()
        self.my_status = monitor.instance_data
        self.check_stability()
        self.my_status_lock.release()

    def check_stability(self):
        self.my_status_lock.acquire()
        if self.my_status.cpu_utilization > 90:
            self.instance_stable = False
        elif self.my_status.memory_utilization > 90:
            self.instance_stable = False
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
                if data.misc_message:  # run restore checkpoint
                    ret = subprocess.call(
                        shlex.split(
                            "../checkpoint-restore "
                            + " ".join(
                                [checkpoint_name]
                            )
                        )
                    )
                    if ret != 0:
                        print("Checkpoint-restore unsuccessful")

                self.all_node_status_lock.acquire()
                self.all_node_status[data.sender_ip] = (
                    data.get_cpu_utilization(),
                    data.get_memory_utilization(),
                    data.get_network_utilization(),
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

    def get_candidate_target(self) -> str:
        # TODO
        pass

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
                    [checkpoint_name, container_name,
                        pem_dir, checkpoint_dir, node_ip]
                )
            )
        )

        if ret == 1:
            print("Migration unsuccessful")
            return (None, False)

        return (ret, True)


config = configparser.ConfigParser()
config.read("../config.ini")
node = Node(config["DEFAULT"]["IP"], config["DEFAULT"]["PORT"])

recv_sos = Value("i", 1)

receiver_process = Process(target=node.recv, args=(recv_sos))
receiver_process.start()
status_update_process = Process(target=node.update_my_status)
status_update_process.start()

while True:
    while node.instance_stable:
        pass

    recv_sos.value = 0

    for node_ip, node_port in NODES.items():
        sender = Sender(node_ip, node_port)
        sender.send(sos=True)

    while recv_sos.value == 0:
        pass

    candidate_target = node.get_candidate_target()
    checkpoint_name = node.migrate(
        candidate_target,
    )  # TODO
    node.instance_stable = True
    checkpoint_name_sender = Sender(candidate_target, NODES[candidate_target])
    checkpoint_name_sender.send(
        data=InstanceData(misc_message=checkpoint_name))
