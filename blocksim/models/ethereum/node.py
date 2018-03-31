from blocksim.models.node import Node
from blocksim.models.network import Network
from blocksim.models.ethereum.message import Message

class ETHNode(Node):
    def __init__(self, env, network: Network, transmission_speed, location: str, address: str):
        super().__init__(env, network, transmission_speed, location, address)

    def send_transactions(self, transactions: list, neighbor_address: str, upload_rate):
        """Send transactions to a neighbor and mark the hashes as known by the neighbor"""
        print(super()._get_neighbor(neighbor_address))
        for tx in transactions:
            super()._mark_transaction(tx.hash, neighbor_address)
        transactions_msg = Message(self).transactions(transactions)
        self.env.process(super().send(neighbor_address, upload_rate, transactions_msg))

    def send_block_headers(self, request: dict, request_address: str, upload_rate):
        """Send block headers for any node that request it, identified by the `request_address`
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
        self.send(request_address, upload_rate, block_headers_msg)

    def send_block_bodies(self, request: dict, request_address: str, upload_rate):
        """Send block bodies for any node that request it, identified by the `request_address`
        ```
        request = { 
            hashes
        }
        ```
        """
        hashes = request.get('hashes')

        block_bodies = []
        for block_hash in hashes:
            block = self.chain.get_block(block_hash)
            block_bodies.append(block)

        block_bodies_msg = Message(self).block_bodies(block_bodies)
        self.send(request_address, upload_rate, block_bodies_msg)
