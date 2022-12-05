from collections import defaultdict
from multiprocessing import Value
from configparser import ConfigParser

NODE_SELECTION_THRESHOLD_CPU_UTILIZATION = 50
NODE_SELECTION_THRESHOLD_MEMORY_UTILIZATION = 50
NODE_SELECTION_THRESHOLD = 1.5


NODES = defaultdict(int)
config = ConfigParser()
config.read("config.ini")
for section in config.sections():
    NODES[config[section]["IP"]] = int(config[section]["PORT"])

MY_IP, MY_PORT = config["DEFAULT"]["IP"], int(config["DEFAULT"]["PORT"])

recv_sos = Value("i", 1)
