from blocksim.models.storage import Storage
from blocksim.models.consensus import apply_block
from blocksim.exceptions import VerificationFailed, InvalidTransaction

class Chain:
    """ Defines the chain model."""
    def __init__(self, genesis=None):
        self.storage = Storage()
        if genesis is None:
            raise Exception("Need genesis block!")
        self.genesis = genesis
        self.storage.put('block:{}'.format(genesis.header.number), genesis.header.hash)
        self.storage.put(genesis.header.hash, genesis)
        self.head_hash = genesis.header.hash
        self.parent_queue = {}

    @property
    def head(self):
        """Head (tip) of the chain"""
        block = self.storage.get(self.head_hash)
        # TODO: The hash of the best (i.e. highest score) known block.
        return block

    def get_parent(self, block):
        # Genesis Block do not have parent
        if block.header.number == 0:
            return None
        return self.get_block(block.header.prevhash)

    def get_block(self, block_hash):
        return self.storage.get(block_hash)

    def get_blockhash_by_number(self, number):
        """Gets the hash of the block with the given block number"""
        try:
            return self.storage.get('block:{}'.format(number))
        except BaseException:
            return None

    def get_block_by_number(self, number):
        """Gets the block with the given block number"""
        return self.get_block(self.get_blockhash_by_number(number))

    def add_block(self, block):
        """Call upon receiving a block"""
        # Is the block being added to the heap?
        if block.header.prevhash == self.head_hash:
            print('Adding block the head', head=block.header.prevhash[:4])
            try:
                # TODO: Send state
                state = {}
                apply_block(state, block)
            except (AssertionError, KeyError, ValueError, InvalidTransaction, VerificationFailed) as e:
                print('Block %d (%s) with parent %s invalid, reason: %s' % (block.header.number, block.header.hash[:4], block.header.prevhash[:4], str(e)))
                return
            self.storage.put('block:{}'.format(block.header.number), block.header.hash)
            self.head_hash = block.header.hash
        # TODO: Or is the block being added to a chain that is not currently the head?
        elif block.header.prevhash in self.storage:
            pass
        # Block has no parent yet
        else:
            if block.header.prevhash not in self.parent_queue:
                self.parent_queue[block.header.prevhash] = []
            self.parent_queue[block.header.prevhash].append(block)
            print('Got block %d (%s) with prevhash %s, parent not found. Delaying for now' % (block.header.number, block.header.hash[:4], block.header.prevhash[:4]))
            return False
        self.add_child(block)

        self.storage.put('head_hash', self.head_hash)

        self.storage.put(block.header.hash, block.header.hash)

        # Are there blocks that we received that were waiting for this block?
        # If so, process them.
        if block.header.hash in self.parent_queue:
            for _blk in self.parent_queue[block.header.hash]:
                self.add_block(_blk)
            del self.parent_queue[block.header.hash]
        return True

    def add_child(self, block):
        print(block)
