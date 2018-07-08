from blocksim.models.ethereum.config import default_config
from blocksim.utils import keccak_256, encode_hex


class BlockHeader:
    """ Defines the BlockHeader model for the Ethereum.

    In this first version of the simulator we do not simulate accounts, transactions merkle trees, uncles blocks, states and receipts

    :param str prevhash: the hash of the previous block
    :param int number: the number of ancestors of this block (0 for the genesis block)
    :param int timestamp: a UNIX timestamp
    :param str coinbase: coinbase address of the block miner, in this simulation we include the node address
    :param int difficulty: the blocks difficulty
    :param int gas_limit: the block's gas limit
    :param int gas_used: the total amount of gas used by all transactions in this block
    :param str nonce: a nonce constituting a Proof-of-Work
    """

    def __init__(self,
                 prevhash=encode_hex(b'\x00' * 32),
                 number=default_config['GENESIS_NUMBER'],
                 timestamp=default_config['GENESIS_TIMESTAMP'],
                 coinbase=encode_hex(b'\x00' * 20),
                 difficulty=default_config['GENESIS_DIFFICULTY'],
                 gas_limit=default_config['GENESIS_GAS_LIMIT'],
                 gas_used=0,
                 nonce=''):
        self.prevhash = prevhash
        self.number = number
        self.timestamp = timestamp
        self.coinbase = coinbase
        self.difficulty = difficulty
        self.gas_limit = gas_limit
        self.gas_used = gas_used
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
        return f'<{self.__class__.__name__}(#{self.number} prevhash:{self.prevhash} timestamp:{self.timestamp} coinbase:{self.coinbase} nonce:{self.nonce})>'

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
