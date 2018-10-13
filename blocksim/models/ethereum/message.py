from blocksim.utils import kB_to_MB


class Message:
    """Defines a model for the network messages of the Ethereum blockchain.

    For each message its calculated the size, taking into account measurements from the live and public network.

    Ethereum Wire Protocol: https://github.com/ethereum/wiki/wiki/Ethereum-Wire-Protocol
    """

    def __init__(self, origin_node):
        self.origin_node = origin_node
        _env = origin_node.env
        self._message_size = _env.config['ethereum']['message_size_kB']

    def status(self):
        """ Inform a peer of its current Ethereum state.
        This message should be sent `after` the initial handshake and `prior` to any ethereum related messages.
        """
        return {
            'id': 'status',
            'protocol_version': 'PV62',
            'network': self.origin_node.network.name,
            'td': self.origin_node.chain.head.header.difficulty,
            'best_hash': self.origin_node.chain.head.header.hash,
            'genesis_hash': self.origin_node.chain.genesis.header.hash,
            'size': kB_to_MB(self._message_size['status'])
        }

    def new_blocks(self, new_blocks: dict):
        """Advertises one or more new blocks which have appeared on the network"""
        num_new_block_hashes = len(new_blocks)
        new_blocks_size = num_new_block_hashes * \
            self._message_size['hash_size']
        return {
            'id': 'new_blocks',
            'new_blocks': new_blocks,
            'size': kB_to_MB(new_blocks_size)
        }

    def transactions(self, transactions: list):
        """ Specify (a) transaction(s) that the peer should make sure is included on its
        transaction queue. Nodes must not resend the same transaction to a peer in the same session.
        This packet must contain at least one (new) transaction.
        """
        num_txs = len(transactions)
        transactions_size = num_txs * self._message_size['tx']
        return {
            'id': 'transactions',
            'transactions': transactions,
            'size': kB_to_MB(transactions_size)
        }

    def get_blocks(self, hashes: list):
        block_bodies_size = len(hashes) * self._message_size['hash_size']
        return {
            'id': 'get_blocks',
            'hashes': hashes,
            'size': kB_to_MB(block_bodies_size)
        }

    def blocks(self, blocks: list):
        """ Reply to `get_blocks`. The items in the list are some of the blocks requested.
        This may contain no items if no blocks were able to be returned for the `get_blocks` message.
        """
        txs_count = 0
        for block in blocks:
            txs_count += block.transaction_count
        # Calculate the size for each tx in each block, block bodie and header
        msg_total_txs_size = txs_count * self._message_size['tx']
        msg_block_bodies_size = len(
            blocks) * self._message_size['block_bodies']
        msg_block_header_size = len(blocks) * self._message_size['header']
        message_size = msg_total_txs_size + msg_block_bodies_size + msg_block_header_size
        print(
            f'Blocks Message with {len(blocks)} blocks; {txs_count} txs; have a message size: {message_size} kB')
        return {
            'id': 'blocks',
            'blocks': blocks,
            'size': kB_to_MB(message_size)
        }
