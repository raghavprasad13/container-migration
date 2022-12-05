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
        data = ""
        conn, addr = self.sock.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                chunk = conn.recv()
                print(f"chunk: {chunk}")
                if not chunk:
                    break
                data += chunk
            print("finished receiving data")

        return loads(data)
