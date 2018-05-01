from blocksim.utils import keccak_256, encode_hex


class BlockHeader:
    """ Defines a basic BlockHeader model.

    :param str prevhash: the hash of the previous block
    :param str tx_list_root: the root of the block's transaction trie
    :param int number: the number of ancestors of this block (0 for the genesis block)
    :param int timestamp: a UNIX timestamp
    :param int difficulty: the blocks difficulty
    :param str nonce: a nonce constituting a Proof-of-Work
    """

    def __init__(self,
                 prevhash=encode_hex(b'\x00' * 32),
                 tx_list_root='681afa780d17da29203322b473d3f210a7d621259a4e6ce9e403f5a266ff719a',
                 number=0,
                 timestamp=0,
                 difficulty=1,
                 nonce=''):
        self.prevhash = prevhash
        self.tx_list_root = tx_list_root
        self.number = number
        self.timestamp = timestamp
        self.difficulty = difficulty
        self.nonce = nonce

    @property
    def hash(self):
        """The block header hash"""
        return encode_hex(keccak_256(str(self).encode('utf-8')))

    def __repr__(self):
        """Returns a unambiguous representation of the block header"""
        return f'<{self.__class__.__name__}(#{self.number} {self.hash})>'

    def __str__(self):
        """Returns a readable representation of the block"""
        return f'<{self.__class__.__name__}(#{self.number} prevhash:{self.prevhash} tx_list_root:{self.tx_list_root} timestamp:{self.timestamp} nonce:{self.nonce})>'

    def __eq__(self, other):
        """Two blocks are equal iff they have the same hash."""
        return isinstance(other, self.__class__) and self.hash == other.hash

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.hash


class Block:
    """ Defines the Block model.

    :param header: the block header
    :param transactions: a list of transactions
    """

    def __init__(self, header: BlockHeader, transactions=None):
        self.header = header
        self.transactions = transactions

    @property
    def transaction_count(self):
        return len(self.transactions)
