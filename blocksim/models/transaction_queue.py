import simpy
from blocksim.utils import time


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
            f'{self.node.address} at {time(self.env)}: Transaction {tx.hash[:8]} added to the queue')

    def put(self, tx):
        self.env.process(self.validate_tx(tx))

    def get(self):
        # TODO: A delay to retrieve a transaction from the Queue
        return self.store.get()
