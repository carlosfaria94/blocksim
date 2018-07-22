import simpy


class Network:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self._nodes = {}

    def get_node(self, address):
        return self._nodes.get(address)

    def add_node(self, node):
        self._nodes[node.address] = node


class Connection:
    """This class represents the propagation through a Connection."""

    def __init__(self, env, origin_node, destination_node):
        self.env = env
        self.store = simpy.Store(env)
        self.origin_node = origin_node
        self.destination_node = destination_node

    def latency(self, envelope):
        # TODO: Professor: Onde é aplicado o delay/RTT/ping? Ao calcular transmission_delay?
        yield self.env.timeout(2)
        self.store.put(envelope)

    def put(self, envelope):
        print(
            f'{envelope.origin.address} at {envelope.timestamp}: Message (ID: {envelope.msg["id"]}) sent with {envelope.msg["size"]} MB with a destination: {envelope.destination.address}')
        self.env.process(self.latency(envelope))

    def get(self):
        return self.store.get()
