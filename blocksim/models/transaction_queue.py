import simpy


class TransactionQueue():
    def __init__(self, env, node):
        self.env = env
        self.node = node
        self.store = simpy.PriorityStore(env)

    def validate_tx(self, tx):
        yield self.env.timeout(self.env.delays['VALIDATE_TX'])
        self.store.put(tx)
        print('{} at {}: Transaction {} added to the queue'
              .format(
                  self.node.address,
                  self.env.now,
                  tx.hash[:8]
              ))

    def put(self, tx):
        self.env.process(self.validate_tx(tx))

    def get(self):
        return self.store.get()
