import simpy
from blocksim.utils import get_random_values


class TransactionQueue():
    def __init__(self, env, node, consensus):
        self.env = env
        self.node = node
        self.consensus = consensus
        self.store = simpy.PriorityStore(env)

    def validate_tx(self, tx):
        # Calculates the delay to validate the tx
        tx_validation_delay = self.consensus.validate_transaction()
        yield self.env.timeout(tx_validation_delay)
        self.store.put(tx)
        print(
            f'{self.node.address} at {self.env.now}: Transaction {tx.hash[:8]} added to the queue')

    def put(self, tx):
        self.env.process(self.validate_tx(tx))

    def get(self):
        return self.store.get()
