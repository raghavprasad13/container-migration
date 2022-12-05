from socket import socket, AF_INET, SOCK_STREAM
from system_data.instance_data import InstanceData
from pickle import dumps
from typing import Optional
from utils.const_and_glob import *


class Sender:
    def __init__(self, receiver_ip: str, receiver_port: int) -> None:
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.receiver_ip = receiver_ip
        self.receiver_port = receiver_port

    def send(self, sos: bool = False, data: Optional[InstanceData] = None) -> None:
        self.sock.connect((self.receiver_ip, self.receiver_port))
        if sos:
            print("sending sos now")
            self.sock.send(dumps(InstanceData((MY_IP, MY_PORT), sos=True)))
        elif data:
            self.sock.send(dumps(data))
