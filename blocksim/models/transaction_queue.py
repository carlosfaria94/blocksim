import simpy
from blocksim.utils import get_random_values


class TransactionQueue():
    def __init__(self, env, node):
        self.env = env
        self.node = node
        self.store = simpy.PriorityStore(env)

    def validate_tx(self, tx):
        tx_validation_delay = round(get_random_values(
            self.env.delays['VALIDATE_TX'])[0], 2)
        yield self.env.timeout(tx_validation_delay)
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
