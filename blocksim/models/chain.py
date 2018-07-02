import random
from blocksim.models.consensus import apply_block, validate_block, apply_transaction, validate_transaction
from blocksim.exceptions import VerificationFailed, InvalidTransaction


class Chain:
    """ Defines the chain model."""

    def __init__(self, env, genesis, db):
        self.env = env
        self.db = db
        self.genesis = genesis
        self.db.put('block:{}'.format(
            genesis.header.number), genesis.header.hash)
        self.db.put(genesis.header.hash, genesis)
        self._head_hash = genesis.header.hash
        self.parent_queue = {}

    @property
    def head(self):
        """Block in the head (tip) of the chain"""
        block = self.db.get(self._head_hash)
        return block

    def get_parent(self, block):
        """Genesis Block do not have parent"""
        if block.header.number == 0:
            return None
        return self.get_block(block.header.prevhash)

    def get_block(self, block_hash):
        """Gets the block with a given block hash"""
        try:
            return self.db.get(block_hash)
        except BaseException:
            return None

    def get_blockhash_by_number(self, number):
        """Gets the hash of the block with the given block number"""
        try:
            return self.db.get(f'block:{number}')
        except BaseException:
            return None

    def get_block_by_number(self, number):
        """Gets the block with the given block number"""
        return self.get_block(self.get_blockhash_by_number(number))

    def add_child(self, child):
        """Add a record allowing you to later look up the provided block's
        parent hash and see that it is one of its children"""
        try:
            existing = self.db.get('child:' + child.header.prevhash)
        except BaseException:
            existing = ''
        existing_hashes = []
        for i in range(0, len(existing), 32):
            existing_hashes.append(existing[i: i + 32])
        if child.header.hash not in existing_hashes:
            self.db.put(
                'child:' + child.header.prevhash,
                existing + child.header.hash)

    def get_child_hashes(self, block_hash):
        """Get the hashes of all known children of a given block"""
        child_hashes = []
        try:
            data = self.db.get('child:' + block_hash)
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
        validate_block(self.env, 3)
        # Is the block being added to the heap?
        if block.header.prevhash == self._head_hash:
            print(
                f'at {self.env.now}: Adding block #{block.header.number} ({block.header.hash[:4]}) to the head', )
            apply_block(self.env, 2)
            self.db.put(f'block:{block.header.number}', block.header.hash)
            self._head_hash = block.header.hash
        # Or is the block being added to a chain that is not currently the head?
        elif block.header.prevhash in self.db:
            print(
                f'Receiving block #{block.header.number} ({block.header.hash[:4]}) not on head ({self._head_hash[:4]}), adding to secondary post state {block.header.prevhash[:4]}')
            apply_block(self.env, 2)
            # TODO: If the block should be the new head, replace the head
            # if block_score > self.get_score(self.head):
            # pass
        # Block has no parent yet
        else:
            if block.header.prevhash not in self.parent_queue:
                self.parent_queue[block.header.prevhash] = []
            self.parent_queue[block.header.prevhash].append(block)
            print(
                f'Got block #{block.header.number} ({block.header.hash[:4]}) with prevhash {block.header.prevhash[:4]}, parent not found. Delaying for now')
            return False

        self.add_child(block)

        self.db.put(block.header.hash, block)

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
        for i in range(max_num - 1):  # We already have one block added to the hashes list
            block = self.get_block(header.prevhash)
            if block is None:
                break
            header = block.header
            hashes.append(header.hash)
            if header.number == 0:
                break
        return hashes
