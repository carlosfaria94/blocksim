from blocksim.utils import encode_hex
from blocksim.models.block import BlockHeader as BaseBlockHeader
from blocksim.models.block import Block as BaseBlock


class BlockHeader(BaseBlockHeader):
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
                 number=0,
                 timestamp=0,
                 coinbase=encode_hex(b'\x00' * 20),
                 difficulty=100000,
                 gas_limit=3000000,
                 gas_used=0,
                 nonce=''):
        super().__init__(prevhash, number, timestamp, coinbase, difficulty, nonce)
        self.gas_limit = gas_limit
        self.gas_used = gas_used


class Block(BaseBlock):
    def __init__(self, header: BlockHeader, transactions=None):
        super().__init__(header, transactions)
