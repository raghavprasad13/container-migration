from socket import socket
from pickle import loads
from server_data import InstanceData


class Receiver:
    def __init__(self) -> None:
        self.sock = socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ""
        self.port = 8080

        self.sock.bind((self.ip, self.port))
        self.sock.listen()

    def receive(self) -> InstanceData:
        data = ""
        conn, addr = self.sock.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                chunk = conn.recv()
                if not chunk:
                    break
                data += chunk

        return loads(data)
