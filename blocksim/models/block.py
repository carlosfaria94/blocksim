from blocksim.utils import keccak_256, encode_hex

class Block:
    """ Defines the block model.

    It is only defined the parameters which we think is common across different blockchains.
    Use :attr:`Block.kwargs` to define other parameters for the model.

    :param str prevhash: the hash of the previous block
    :param str tx_list_root: the root of the block's transaction trie
    :param int number: the number of ancestors of this block (0 for the genesis block)
    :param int timestamp: a UNIX timestamp
    :param str nonce: a nonce constituting a proof-of-work, or the empty string as a placeholder
    :param transactions: a list of transactions

    """
    def __init__(self,
                prevhash='',
                tx_list_root='',
                number=0,
                timestamp=0,
                nonce='',
                transactions=dict(),
                **kwargs):
        self.prevhash = prevhash
        self.tx_list_root = tx_list_root
        self.number = number
        self.timestamp = timestamp
        self.nonce = nonce
        self.transactions = transactions
        for key in kwargs:
            print("another parameters: %s: %s" % (key, kwargs[key]))

    @property
    def hash(self):
        """The block hash"""
        return encode_hex(keccak_256(str(self).encode('utf-8')))

    def __repr__(self):
        """Returns a unambiguous representation of the block"""
        return '<{}(#{} {})>'.format(self.__class__.__name__, self.number, self.hash)

    def __str__(self):
        """Returns a readable representation of the block"""
        return f'<{self.__class__.__name__}(#{self.number} prevhash:{self.prevhash} tx_list_root:{self.tx_list_root} timestamp:{self.timestamp} nonce:{self.nonce})>'

    def __eq__(self, other):
        """Two blocks are equal iff they have the same hash."""
        return isinstance(other, Block) and self.hash == other.hash

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.hash
