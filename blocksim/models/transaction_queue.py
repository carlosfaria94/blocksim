import simpy

class TransactionQueue():
    def __init__(self, env, delay, node):
        self.env = env
        self.delay = delay
        self.node = node
        self.store = simpy.PriorityStore(env)

    def latency(self, tx):
        yield self.env.timeout(self.delay)
        self.store.put(tx)
        print('{} at {}: Transaction {} added to the queue'
            .format(
                self.node.address,
                self.env.now,
                tx.hash[:8]
            ))

    def put(self, tx):
        self.env.process(self.latency(tx))

    def get(self):
        return self.store.get()
