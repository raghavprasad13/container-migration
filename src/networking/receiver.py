from socket import socket, AF_INET, SOCK_STREAM
from pickle import loads
from system_data.instance_data import InstanceData
from configparser import ConfigParser


class Receiver:
    def __init__(self) -> None:
        self.sock = socket(AF_INET, SOCK_STREAM)
        config = ConfigParser()
        config.read("config.ini")
        self.ip = config["DEFAULT"]["IP"]
        self.port = int(config["DEFAULT"]["PORT"])

        self.sock.bind((self.ip, self.port))
        self.sock.listen()

    def receive(self) -> InstanceData:
        data = None
        conn, _ = self.sock.accept()
        with conn:
            chunk = conn.recv(4096)
            data = chunk

        return loads(data)
