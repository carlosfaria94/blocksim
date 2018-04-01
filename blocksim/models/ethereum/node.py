from blocksim.models.node import Node
from blocksim.models.network import Network
from blocksim.models.ethereum.message import Message

class ETHNode(Node):
    def __init__(self, env, network: Network, transmission_speed, location: str, address: str):
        super().__init__(env, network, transmission_speed, location, address)

    def send_transactions(self, transactions: list, upload_rate):
        """Send/Broadcast transactions to all neighbors and mark the hashes as known
        by each neighbor"""
        for neighbor_address, neighbor in self.neighbors.items():
            neighbor_known_txs = neighbor.get('knownTxs')
            for tx in transactions:
                # Checks if the transaction was previous sent
                if any({tx.hash} & neighbor_known_txs):
                    print('{} at {}: Transaction {} was already sent to {}'.format(
                        self.address, self.env.now, tx.hash[:8], neighbor_address))
                    transactions.remove(tx)
                else:
                    self._mark_transaction(tx.hash, neighbor_address)

            print('{} at {}: Transactions ready to sent: {}'.format(
                self.address, self.env.now, transactions))
            transactions_msg = Message(self).transactions(transactions)
            self.env.process(self.send(neighbor_address, upload_rate, transactions_msg))

    def send_block_headers(self, request: dict, destination_address: str, upload_rate):
        """Send block headers for any node that request it, identified by the `destination_address`
        ```
        request = { 
            block_number,
            max_headers,
            reverse
        }
        ```
        """
        block_number = request.get('block_number', 0)
        max_headers = request.get('max_headers', 1)
        reverse = request.get('reverse', 1)

        block_hash = self.chain.get_blockhash_by_number(block_number)
        block_hashes = self.chain.get_blockhashes_from_hash(block_hash, max_headers)

        block_headers = []
        for _block_hash in block_hashes:
            block_header = self.chain.get_block(_block_hash).header
            block_headers.append(block_header)
        if reverse == 0:
            block_headers.reverse()

        block_headers_msg = Message(self).block_headers(block_headers)
        self.env.process(super().send(destination_address, upload_rate, block_headers_msg))

    def send_block_bodies(self, request: dict, destination_address: str, upload_rate):
        """Send block bodies for any node that request it, identified by the `destination_address`.

        In `request['hashes']` we obtain a list of hashes of block bodies being requested
        """
        hashes = request.get('hashes')

        block_bodies = []
        for block_hash in hashes:
            block = self.chain.get_block(block_hash)
            block_bodies.append(block)

        block_bodies_msg = Message(self).block_bodies(block_bodies)
        self.env.process(self.send(destination_address, upload_rate, block_bodies_msg))

    def request_headers(self,
                        block_number: int,
                        max_headers: int,
                        reverse: int,
                        destination_address: str,
                        upload_rate):
        """Request a node (identified by the `destination_address`) to return block headers.

        Request must contain a number of block headers, of rising number when `reverse` is `0`,
        falling when `1`, beginning at `block_number`.
        At most `max_headers` items.
        """
        get_block_headers_msg = Message(self).get_block_headers(block_number, max_headers, reverse)
        self.env.process(self.send(destination_address, upload_rate, get_block_headers_msg))

    def request_bodies(self, hashes: list, destination_address: str, upload_rate):
        """Request a node (identified by the `destination_address`) to return block bodies.
        Specify a list of `hashes` that we're interested in.
        """
        get_block_bodies_msg = Message(self).get_block_bodies(hashes)
        self.env.process(self.send(destination_address, upload_rate, get_block_bodies_msg))

