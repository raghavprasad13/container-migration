from sender import Sender
from receiver import Receiver
from collections import defaultdict
from multiprocessing import Process, Value
from threading import Lock
from system_data.instance_data import InstanceData


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

    def update_my_status(self, status: InstanceData):
        self.my_status_lock.acquire()
        self.my_status = status
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
        pass

    def migrate(self, node_ip: str) -> bool:
        pass


node = Node("", 8080)

recv_sos = Value("i", 1)

receiver_process = Process(target=node.recv, args=(recv_sos))
receiver_process.start()
status_update_process = Process(target=node.update_my_status, args=("""TODO"""))
status_update_process.start()

while True:
    while node.instance_stable:
        pass

    recv_sos.value = 0

    for node_ip, node_port in NODES.items():
        sender = Sender(node_ip, node_port)
        sender.send(sos=True)

    node.node_recv_progress_lock.acquire()
    node.node_recv_progress = {node_ip: False for node_ip in NODES}
    node.node_recv_progress_lock.release()

    while recv_sos.value == 0:
        pass

    candidate_target = node.get_candidate_target()
    node.migrate(candidate_target)
    node.instance_stable = True
