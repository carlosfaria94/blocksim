import random
from blocksim.models.storage import Storage
from blocksim.models.consensus import apply_block
from blocksim.exceptions import VerificationFailed, InvalidTransaction

class Chain:
    """ Defines the chain model."""
    def __init__(self, genesis):
        self.storage = Storage()
        self.genesis = genesis
        self.storage.put('block:{}'.format(genesis.header.number), genesis.header.hash)
        self.storage.put(genesis.header.hash, genesis)
        self._head_hash = genesis.header.hash
        self.parent_queue = {}

    @property
    def head(self):
        """Block in the head (tip) of the chain"""
        block = self.storage.get(self._head_hash)
        return block

    def get_parent(self, block):
        """Genesis Block do not have parent"""
        if block.header.number == 0:
            return None
        return self.get_block(block.header.prevhash)

    def get_block(self, block_hash):
        """Gets the block with a given block hash"""
        try:
            return self.storage.get(block_hash)
        except BaseException:
            return None

    def get_blockhash_by_number(self, number):
        """Gets the hash of the block with the given block number"""
        try:
            return self.storage.get(f'block:{number}')
        except BaseException:
            return None

    def get_block_by_number(self, number):
        """Gets the block with the given block number"""
        return self.get_block(self.get_blockhash_by_number(number))

    def add_child(self, child):
        """Add a record allowing you to later look up the provided block's
        parent hash and see that it is one of its children"""
        try:
            existing = self.storage.get('child:' + child.header.prevhash)
        except BaseException:
            existing = ''
        existing_hashes = []
        for i in range(0, len(existing), 32):
            existing_hashes.append(existing[i: i + 32])
        if child.header.hash not in existing_hashes:
            self.storage.put(
                'child:' + child.header.prevhash,
                existing + child.header.hash)

    def get_child_hashes(self, block_hash):
        """Get the hashes of all known children of a given block"""
        child_hashes = []
        try:
            data = self.storage.get('child:' + block_hash)
            for i in range(0, len(data), 32):
                child_hashes.append(data[i:i + 32])
            return child_hashes
        except BaseException:
            return []

    def get_children(self, block):
        """Get the children of a block"""
        return [self.get_block(h) for h in self.get_child_hashes(block.header.hash)]

    def add_block(self, block):
        """Call upon receiving a block"""
        # Is the block being added to the heap?
        if block.header.prevhash == self._head_hash:
            print(f'Adding block ({block.header.hash[:16]}) to the head', )
            try:
                # TODO: Send state
                state = {}
                apply_block(state, block)
            except (AssertionError, KeyError, ValueError, InvalidTransaction, VerificationFailed) as e:
                print('Block %d (%s) with parent %s invalid, reason: %s' % (block.header.number, block.header.hash[:4], block.header.prevhash[:4], str(e)))
                return False
            self.storage.put(f'block:{block.header.number}', block.header.hash)
            self._head_hash = block.header.hash
        # Or is the block being added to a chain that is not currently the head?
        elif block.header.prevhash in self.storage:
            print('Receiving block %d (%s) not on head (%s), adding to secondary post state %s' % (block.header.number, block.header.hash[:4], self._head_hash[:4], block.header.prevhash[:4]))
            try:
                temp_state = {}
                apply_block(temp_state, block)
            except (AssertionError, KeyError, ValueError, InvalidTransaction, VerificationFailed) as e:
                print(f'Block {block.header.hash[:4]} with parent {block.header.prevhash[:4]} invalid, reason: {str(e)}')
                return False
            # TODO: If the block should be the new head, replace the head
            #if block_score > self.get_score(self.head):
                #pass
        # Block has no parent yet
        else:
            if block.header.prevhash not in self.parent_queue:
                self.parent_queue[block.header.prevhash] = []
            self.parent_queue[block.header.prevhash].append(block)
            print('Got block %d (%s) with prevhash %s, parent not found. Delaying for now' % (block.header.number, block.header.hash[:4], block.header.prevhash[:4]))
            return False

        self.add_child(block)

        self.storage.put(block.header.hash, block)

        # Are there blocks that we received that were waiting for this block?
        # If so, process them.
        if block.header.hash in self.parent_queue:
            for _block in self.parent_queue[block.header.hash]:
                self.add_block(_block)
            del self.parent_queue[block.header.hash]
        return True

    def __contains__(self, block):
        try:
            o = self.get_blockhash_by_number(block.number)
            assert o == block.hash
            return True
        except Exception as e:
            return False

    def get_blockhashes_from_hash(self, block_hash, max_num):
        """Get blockhashes starting from a hash and going backwards"""
        block = self.get_block(block_hash)
        if block is None:
            return []

        header = block.header
        hashes = []
        hashes.append(block.header.hash)
        for i in range(max_num - 1): # We already have one block added to the hashes list
            block = self.get_block(header.prevhash)
            if block is None:
                break
            header = block.header
            hashes.append(header.hash)
            if header.number == 0:
                break
        return hashes
