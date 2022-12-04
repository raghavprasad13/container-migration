from collections import defaultdict
from multiprocessing import Value

NODE_SELECTION_THRESHOLD_CPU_UTILIZATION = 50
NODE_SELECTION_THRESHOLD_MEMORY_UTILIZATION = 50
NODE_SELECTION_THRESHOLD = 1.5

NODES = defaultdict(int)

recv_sos = Value("i", 1)
