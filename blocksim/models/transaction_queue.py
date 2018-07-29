from collections import deque
from blocksim.utils import time


class TransactionQueue():
    def __init__(self, env, node, consensus):
        self._env = env
        self._node = node
        self._consensus = consensus
        self._transaction_queue = deque([])

    def validate_tx(self, tx):
        # Calculates the delay to validate the tx
        tx_validation_delay = self._consensus.validate_transaction()
        yield self._env.timeout(tx_validation_delay)

    def put(self, tx):
        self._env.data['number_of_transactions_queue'] += 1
        self._env.process(self.validate_tx(tx))
        # TODO: Order the list according to the fee
        self._transaction_queue.append(tx)
        print(
            f'{self._node.address} at {time(self._env)}: Transaction {tx.hash[:8]} added to the queue {self}')

    def get(self):
        # TODO: A delay to retrieve a transaction from the Queue
        return self._transaction_queue.popleft()

    def is_empty(self):
        return len(self._transaction_queue) == 0

    def size(self):
        return len(self._transaction_queue)
