from networking.sender import Sender
from multiprocessing import Process, Value
from node import Node
from system_data.instance_data import InstanceData
from configparser import ConfigParser
from utils.const_and_glob import *


if __name__ == "__main__":
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
        checkpoint_name_sender = Sender(
            candidate_target, NODES[candidate_target])
        checkpoint_name_sender.send(
            data=InstanceData(misc_message=checkpoint_name))
