from typing import Optional, Tuple


class InstanceData:
    def __init__(
        self,
        sender_ip_port: Tuple[str, int],
        cpu_utilization: Optional[float] = None,
        memory_utilization: Optional[float] = None,
        network_utilization: Optional[float] = None,
        cpu: Optional[float] = None,
        memory: Optional[float] = None,
        sos: bool = False,
        misc_message: Optional[str] = None,
    ) -> None:
        self.sender_ip, self.sender_port = sender_ip_port
        self.cpu_utilization = cpu_utilization
        self.memory_utilization = memory_utilization
        self.network_utilization = network_utilization
        self.cpu = cpu
        self.memory = memory
        self.sos = sos
        self.misc_message = misc_message

    def __repr__(self) -> str:
        d = {
            "sender_ip": self.sender_ip,
            "sender_port": self.sender_port,
            "cpu_utilization": self.cpu_utilization,
            "memory_utilization": self.memory_utilization,
            "network_utilization": self.network_utilization,
            "cpu": self.cpu,
            "memory": self.memory,
            "sos": self.sos,
            "misc_message": self.misc_message,
        }

        repr = ""
        for key, val in d.items():
            if not val:
                continue
            if type(val) == int:
                val = str(val)
            repr += key + ": " + str(val) + ", "
        repr = repr.strip()

        return repr

    def get_cpu_utilization(self) -> float:
        return self.cpu_utilization

    def get_memory_utilization(self) -> float:
        return self.memory_utilization

    def get_network_utilization(self) -> float:
        return self.network_utilization

    def get_cpu(self) -> float:
        return self.cpu

    def get_memory(self) -> float:
        return self.memory
