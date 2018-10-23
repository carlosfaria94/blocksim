from collections import deque
from blocksim.utils import time


class TransactionQueue():
    def __init__(self, env, node, consensus):
        self._env = env
        self._node = node
        self._consensus = consensus
        self._transaction_queue = deque([])
        key = f'{node.address}_number_of_transactions_queue'
        self._env.data[key] = 0

    def put(self, tx):
        key = f'{self._node.address}_number_of_transactions_queue'
        self._env.data[key] += 1
        self._transaction_queue.append(tx)

    def get(self):
        # TODO: A delay to retrieve a transaction from the Queue
        return self._transaction_queue.popleft()

    def is_empty(self):
        return len(self._transaction_queue) == 0

    def size(self):
        return len(self._transaction_queue)
