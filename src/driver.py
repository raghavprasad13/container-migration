from networking.sender import Sender
from multiprocessing import Process, Value
from node import Node, NodeManager, NodeProxy
from system_data.instance_data import InstanceData
from configparser import ConfigParser
from utils.const_and_glob import *


def update_status(node: Node) -> None:
    node.update_my_status()


def recv(sos: Value, node: Node) -> None:
    node.recv(sos)


if __name__ == "__main__":
    config = ConfigParser()
    config.read("config.ini")
    # node = Node(config["DEFAULT"]["IP"], int(config["DEFAULT"]["PORT"]))
    for section in config.sections():
        NODES[config[section]["IP"]] = int(config[section]["PORT"])

    NodeManager.register("Node", Node, NodeProxy)
    with NodeManager() as manager:
        node = manager.Node(config["DEFAULT"]["IP"], int(config["DEFAULT"]["PORT"]))
        # print(type(node))
        recv_sos = Value("i", 1)

        status_update_process = Process(target=update_status, args=(node,))
        status_update_process.start()
        # status_update_process.join()
        receiver_process = Process(
            target=recv,
            args=(
                recv_sos,
                node,
            ),
        )
        receiver_process.start()

        while True:
            print("here")
            while node.cpu_stable and node.memory_stable:
                # print(node.cpu_stable, node.memory_stable)
                print(f"node.my_status: {node.my_status}")
                # print()
                # pass

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
    print("outside")
