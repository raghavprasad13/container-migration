from networking.sender import Sender
from multiprocessing import Process
from node import Node, NodeManager, NodeProxy
from system_data.instance_data import InstanceData
from utils.const_and_glob import *


def update_status(node: Node) -> None:
    node.update_my_status()


def recv(node: Node) -> None:
    node.recv()


if __name__ == "__main__":
    NodeManager.register("Node", Node, NodeProxy)
    with NodeManager() as manager:
        node = manager.Node(MY_IP, MY_PORT)

        receiver_process = Process(
            target=recv,
            args=(node,),
        )
        receiver_process.start()
        status_update_process = Process(target=update_status, args=(node,))
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
            checkpoint_name, migration_status = node.migrate()
            if not migration_status:
                continue

            if not node.cpu_stable:
                node.cpu_stable = True
            if not node.memory_stable:
                node.memory_stable = True
            checkpoint_name_sender = Sender(candidate_target, NODES[candidate_target])
            checkpoint_name_sender.send(
                data=InstanceData((MY_IP, MY_PORT), misc_message=checkpoint_name)
            )
