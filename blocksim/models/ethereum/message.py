class Message:
    """Defines a model for the network messages of the Ethereum blockchain.

    For each message its calculated the size, taking into account measurements from the live and public network.
    """

    def __init__(self, origin_node):
        self.origin_node = origin_node

    # TODO: We need to calculate the real size for each message (we need to measure from a real network)

    def status(self):
        """ Inform a peer of its current Ethereum state.
        This message should be sent `after` the initial handshake and `prior` to any ethereum related messages.
        """
        return {
            'id': 0,
            'protocol_version': 'PV62',
            'network': self.origin_node.network.name,
            'td': self.origin_node.chain.head.header.difficulty,
            'best_hash': self.origin_node.chain.head.header.hash,
            'genesis_hash': self.origin_node.chain.genesis.header.hash,
            'size': 10  # TODO: Measure the size message
        }

    def new_blocks(self, new_blocks: dict):
        return {
            'id': 1,
            'new_blocks': new_blocks,
            'size': 10  # TODO: Measure the size message
        }

    def transactions(self, transactions: list):
        """ Specify (a) transaction(s) that the peer should make sure is included on its
        transaction queue. Nodes must not resend the same transaction to a peer in the same session.
        This packet must contain at least one (new) transaction.
        """
        return {
            'id': 2,
            'transactions': transactions,
            'size': 10  # TODO: Measure the size message
        }

    def get_block_headers(self, block_number: int, max_headers: int, reverse: int):
        return {
            'id': 3,
            'block_number': block_number,
            'max_headers': max_headers,
            'reverse': reverse,
            'size': 10  # TODO: Measure the size message
        }

    def block_headers(self, block_headers: list):
        """ Reply to `get_block_headers` the items in the list are block headers.
        This may contain no block headers if no block headers were able to be returned
        for the `get_block_headers` message.
        """
        return {
            'id': 4,
            'block_headers': block_headers,
            'size': 10  # TODO: Measure the size message
        }

    def get_block_bodies(self, hashes: list):
        return {
            'id': 5,
            'hashes': hashes,
            'size': 10  # TODO: Measure the size message
        }

    def block_bodies(self, block_bodies: dict):
        """ Reply to `get_block_bodies`. The items in the list are some of the blocks, minus the header.
        This may contain no items if no blocks were able to be returned for the `get_block_bodies` message.
        """
        return {
            'id': 6,
            'block_bodies': block_bodies,
            'size': 10  # TODO: Measure the size message
        }
