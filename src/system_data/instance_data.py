from typing import Optional


class InstanceData:
    def __init__(
        self,
        sender_ip_port: tuple[str, int],
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
