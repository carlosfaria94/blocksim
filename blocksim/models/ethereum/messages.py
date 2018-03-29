from blocksim.models.node import Node

class Messages:
    def __init__(self, origin_node: Node):
        self.origin_node = origin_node

    # TODO: We need to calculate the real size for each message (we need to measure from a real network)

    def hello(self):
        """ First packet sent over the connection, and sent once by both sides.
        No other messages may be sent until a Hello is received.
        """
        return {
            'id': 0,
            'size': 10 # TODO: Measure the size message
        }

    def status(self):
        """ Inform a peer of its current Ethereum state.
        This message should be sent `after` the initial handshake and `prior` to any
        ethereum related messages.
        """
        return {
            'id': 1,
            'protocol_version': 'PV62',
            'network_id': 'Frontier',
            'score': self.origin_node.chain.head.header.difficulty,
            'best_hash': self.origin_node.chain.head.header.hash,
            'genesis_hash': self.origin_node.chain.genesis.header.hash,
            'size': 10 # TODO: Measure the size message
        }

    def transactions(self, transactions: list):
        """ Specify (a) transaction(s) that the peer should make sure is included on its
        transaction queue. Nodes must not resend the same transaction to a peer in the same session.
        This packet must contain at least one (new) transaction.
        """
        return {
            'id': 2,
            'transactions': transactions
        }

    def get_block_headers(self, block_number: int, max_headers: int, reverse: int):
        """ Require peer to return a `block_headers` message.
        Reply must contain a number of block headers, of rising number when `reverse` is `0`,
        falling when `1`, `skip` blocks apart, beginning at `block_number`.
        At most `max_headers` items.
        """
        return {
            'id': 3,
            'block_number': block_number,
            'max_headers': max_headers,
            'reverse': reverse,
            'size': 10 # TODO: Measure the size message
        }

    def block_headers(self, request: dict):
        """ Reply to `get_block_headers` the items in the list are block headers.
        This may contain no block headers if no block headers were able to be returned
        for the `get_block_headers` message.
        """
        chain = self.origin_node.chain
        block_headers = []
        block_hash = chain.get_blockhash_by_number(request.block_number)
        block_hashes = chain.get_blockhashes_from_hash(block_hash, request.max_headers)
        for block_hash in block_hashes:
            block_header = chain.get_block(block_hash).header
            block_headers.append(block_header)
        if request.reverse == 0:
            block_headers.reverse()
        return {
            'id': 4,
            'block_headers': block_headers,
            'size': 10 # TODO: Measure the size message
        }

    def get_block_bodies(self, hashes: list):
        """ Require peer to return a `block_bodies` message.
        Specify the set of blocks that we're interested in with the hashes.
        """
        return {
            'id': 5,
            'hashes': hashes,
            'size': 10 # TODO: Measure the size message
        }

    def block_bodies(self, request: dict):
        """ Reply to `get_block_bodies`. The items in the list are some of the blocks, minus the header.
        This may contain no items if no blocks were able to be returned for the `get_block_bodies` message.
        """
        chain = self.origin_node.chain
        block_bodies = []
        for block_hash in request.hashes:
            block = chain.get_block(block_hash)
            block_bodies.append(block)
        return {
            'id': 6,
            'block_bodies': block_bodies,
            'size': 10 # TODO: Measure the size message
        }
