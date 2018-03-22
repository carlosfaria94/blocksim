from blocksim.models.ethereum.config import default_config
from blocksim.utils import keccak_256, encode_hex

class BlockHeader:
    """ Defines the BlockHeader model for the Ethereum.

    :param str prevhash: the hash of the previous block
    :param str tx_list_root: the root of the block's transaction trie
    :param int number: the number of ancestors of this block (0 for the genesis block)
    :param int timestamp: a UNIX timestamp
    :param str uncles_hash: hash of the list of uncle headers
    :param str state_root: the root of the block's state trie
    :param str receipts_root: the root of the block's receipts trie
    :param str coinbase: coinbase address
    :param int difficulty: the blocks difficulty
    :param int gas_limit: the block's gas limit
    :param int gas_used: the total amount of gas used by all transactions in this block
    :param str nonce: a nonce constituting a Proof-of-Work
    """
    def __init__(self,
                prevhash=default_config['GENESIS_PREVHASH'],
                tx_list_root=default_config['BLANK_ROOT'],
                number=default_config['GENESIS_NUMBER'],
                timestamp=default_config['GENESIS_TIMESTAMP'],
                uncles_hash=default_config['BLANK_ROOT'],
                state_root=default_config['BLANK_ROOT'],
                receipts_root=default_config['BLANK_ROOT'],
                coinbase=default_config['GENESIS_COINBASE'],
                difficulty=default_config['GENESIS_DIFFICULTY'],
                gas_limit=default_config['GENESIS_GAS_LIMIT'],
                gas_used=0,
                nonce=''):
        self.prevhash = prevhash
        self.tx_list_root = tx_list_root
        self.number = number
        self.timestamp = timestamp
        self.uncles_hash = uncles_hash
        self.state_root = state_root
        self.receipts_root = receipts_root
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
    def __init__(self, header: BlockHeader, transactions: dict):
        self.header = header
        self.transactions = transactions

    @property
    def transaction_count(self):
        return len(self.transactions)
