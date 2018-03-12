import simpy

class Network:
    def __init__(self, env):
        self.env = env
        self.nodes = dict()

    def get_node(self, address):
        if not self.nodes:
            raise RuntimeError('There are no nodes in the Network.')
        return self.nodes.get(address)

    def set_node(self, node):
        self.nodes[node.address] = node

class Connection:
    """This class represents the propagation through a Connection."""
    def __init__(self, env, origin_node, destination_node):
        self.env = env
        self.store = simpy.Store(env)
        self.delay = 10 # TODO: This depends in the origin and destination
        self.origin_node = origin_node
        self.destination_node = destination_node

    def latency(self, envelope):
        yield self.env.timeout(self.delay)
        self.store.put(envelope)

    def put(self, envelope):
        print('At {}: Message ({}) with {} MB sent by {}, with a destination: {}'
            .format(
                envelope.timestamp,
                envelope.msg,
                envelope.size,
                envelope.origin.address,
                envelope.destination.address
            ))
        self.env.process(self.latency(envelope))

    def get(self):
        return self.store.get()