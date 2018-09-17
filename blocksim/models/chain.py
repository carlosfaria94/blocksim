import random
import itertools
from blocksim.utils import time


class Chain:
    """Defines a base chain model that needs to be extended according to blockchain protocol
    being simulated"""

    def __init__(self, env, node, consensus, genesis, db):
        self.env = env
        self.node = node
        self.consensus = consensus
        self.db = db
        self.genesis = genesis

        # Set the score (AKA total difficulty in PoW)
        self.db.put(f'score:{genesis.header.hash}', "0")

        # Init the chain with the Genesis block
        self.db.put(f'block:{genesis.header.number}', genesis.header.hash)
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

    def get_pow_difficulty(self, block):
        """Get the total difficulty in PoW of a given block"""
        if not block:
            return 0
        key = f'score:{block.header.hash}'
        fills = []
        while key not in self.db:
            fills.insert(0, (block.header.hash, block.header.difficulty))
            key = f'score:{block.header.prevhash}'
            block = self.get_parent(block)
            if block is None:
                return 0
        score = int(self.db.get(key))
        for h, d in fills:
            key = f'score:{h}'
            score = score + d + random.randrange(10**6 + 1)
            self.db.put(key, str(score))
        return score

    def get_children(self, block):
        """Get the children of a block"""
        return [self.get_block(h) for h in self.get_child_hashes(block.header.hash)]

    def add_block(self, block):
        """Call upon receiving a block"""
        # Is the block being added to the heap?
        if block.header.prevhash == self._head_hash:
            print(
                f'{self.node.address} at {time(self.env)}: Adding block #{block.header.number} ({block.header.hash[:8]}) to the head', )
            self.db.put(f'block:{block.header.number}', block.header.hash)
            self._head_hash = block.header.hash
        # Or is the block being added to a chain that is not currently the head?
        elif block.header.prevhash in self.db:
            print(
                f'{self.node.address} at {time(self.env)}: Receiving block #{block.header.number} ({block.header.hash[:8]}) not on head ({self._head_hash[:8]}), adding to secondary chain')
            key = f'forks_{self.node.address}'
            self.env.data[key] += 1
            block_td = self.get_pow_difficulty(block)
            # If the block should be the new head, replace the head
            if block_td > self.get_pow_difficulty(self.head):
                b = block
                new_chain = {}
                # Find common ancestor
                while b.header.number >= 0:
                    new_chain[b.header.number] = b
                    key = f'block:{b.header.number}'
                    orig_at_height = self.db.get(
                        key) if key in self.db else None
                    if orig_at_height == b.header.hash:
                        break
                    if b.header.prevhash not in self.db or self.db.get(
                            b.header.prevhash) == self.genesis.header.hash:
                        break
                    b = self.get_parent(b)
                replace_from = b.header.number
                # Replace block index and transactions

                # Read: for i in range(common ancestor block number...new block
                # number)
                for i in itertools.count(replace_from):
                    print(
                        f'{self.node.address} at {time(self.env)}: Rewriting height {i}')
                    key = f'block:{i}'
                    # Delete data for old blocks
                    orig_at_height = self.db.get(
                        key) if key in self.db else None
                    if orig_at_height:
                        orig_block_at_height = self.get_block(orig_at_height)
                        print(
                            f'{self.node.address} at {time(self.env)}: {orig_block_at_height.header.hash} no longer in main chain')
                        # Delete from block index
                        self.db.delete(key)
                    # Add data for new blocks
                    if i in new_chain:
                        new_block_at_height = new_chain[i]
                        print(
                            f'{self.node.address} at {time(self.env)}: {new_block_at_height.header.hash} now in main chain')
                        # Add to block index
                        self.db.put(key, new_block_at_height.header.hash)
                    if i not in new_chain and not orig_at_height:
                        break
                self._head_hash = block.header.hash
        # Block has no parent yet. An Orphan block
        else:
            if block.header.prevhash not in self.parent_queue:
                self.parent_queue[block.header.prevhash] = []
            self.parent_queue[block.header.prevhash].append(block)
            print(
                f'{self.node.address} at {time(self.env)}: Got block #{block.header.number} ({block.header.hash[:8]}) with prevhash {block.header.prevhash[:8]}, parent not found. Delaying for now')
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
