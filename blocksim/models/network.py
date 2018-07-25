from random import randint
import simpy
from blocksim.utils import get_random_values, random_pick, time


class Network:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.total_hashrate = 0
        self._nodes = {}
        self._list_nodes = []
        self._list_probabilities = []

    def get_node(self, address):
        return self._nodes.get(address)

    def add_node(self, node):
        self._nodes[node.address] = node
        self.total_hashrate += node.hashrate

    def _init_lists(self):
        for add, node in self._nodes.items():
            if node.is_mining:
                self._list_nodes.append(node)
                node_prob = node.hashrate / self.total_hashrate
                self._list_probabilities.append(node_prob)

    def start_heartbeat(self):
        """During all the simulation its choosen 1 or 2 nodes to broadcast a candidate block.

        1 or 2 nodes are chosen only when a certain delay is passed. This delay simulates
        the time between blocks on the chosen blockchain.

        Each node has a corresponding hashrate. The greater the hashrate, the greater the
        probability of the node being chosen.
        """
        self._init_lists()
        while True:
            time_between_blocks = round(get_random_values(
                self.env.delays['TIME_BETWEEN_BLOCKS'])[0], 2)
            yield self.env.timeout(time_between_blocks)
            how_many_nodes = randint(1, 2)
            selected_nodes = []
            for i in range(how_many_nodes):
                chosen = random_pick(
                    self._list_nodes, self._list_probabilities)
                if chosen in selected_nodes:
                    break
                selected_nodes.append(chosen)
                print(
                    f'Network at {time(self.env)}: Node {chosen.address} chosen to broadcast his candidate block')
                # Give orders to the choosen node to broadcast his candidate block
                self.env.process(chosen.build_new_block())


class Connection:
    """This class represents the propagation through a Connection."""

    def __init__(self, env, origin_node, destination_node):
        self.env = env
        self.store = simpy.Store(env)
        self.origin_node = origin_node
        self.destination_node = destination_node

    def latency(self, envelope):
        # TODO: Onde é aplicado o delay/RTT/ping? Ao calcular transmission_delay?
        yield self.env.timeout(2)
        self.store.put(envelope)

    def put(self, envelope):
        print(
            f'{envelope.origin.address} at {envelope.timestamp}: Message (ID: {envelope.msg["id"]}) sent with {envelope.msg["size"]} MB with a destination: {envelope.destination.address}')
        self.env.process(self.latency(envelope))

    def get(self):
        return self.store.get()
