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
        self.delay = 10 # TODO: This depends in the origin and destination
        self.origin_node = origin_node
        self.destination_node = destination_node

    def latency(self, envelope):
        yield self.env.timeout(self.delay)
        self.store.put(envelope)

    def put(self, envelope):
        print('{} at {}: Message (ID: {}) sent with {} MB sent by {}, with a destination: {}'
            .format(
                envelope.origin.address,
                envelope.timestamp,
                envelope.msg,
                envelope.msg['size'],
                envelope.origin.address,
                envelope.destination.address
            ))
        self.env.process(self.latency(envelope))

    def get(self):
        return self.store.get()
