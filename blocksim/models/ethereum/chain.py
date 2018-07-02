import random
from blocksim.models.chain import Chain


class ETHChain(Chain):
    """Defines a model for the Ethereum chain logic and rules"""

    def __init__(self, env, node, consensus, genesis, db):
        super().__init__(env, node, consensus, genesis, db)

        # Set the score (AKA total difficulty in PoW)
        db.put(f'score:{genesis.header.hash}', "0")

    def get_pow_difficulty(self, block):
        """Get the total difficulty in PoW of a given block"""
        if not block:
            return 0
        key = f'score:{block.header.hash}'
        fills = []
        while key not in self.db:
            print((block.header.hash, block.header.difficulty, block.header.number))
            fills.insert(0, (block.header.hash, block.header.difficulty))
            key = f'score:{block.header.prevhash}'
            block = self.get_parent(block)
            if block is None:
                return 0
        score = int(self.db.get(key))
        for h, d in fills:
            key = f'score:{h}'
            score = score + d + random.randrange(d // 10**6 + 1)
            self.db.put(key, str(score))
        return score

    def add_block(self, block):
        """Call upon receiving a block"""
        self.consensus.validate_block(self.env, 3)
        # Is the block being added to the heap?
        if block.header.prevhash == self._head_hash:
            print(
                f'{self.node.address} at {self.env.now}: Adding block #{block.header.number} ({block.header.hash[:8]}) to the head', )
            self.consensus.apply_block(self.env, 2)
            self.db.put(f'block:{block.header.number}', block.header.hash)
            self._head_hash = block.header.hash
        # Or is the block being added to a chain that is not currently the head?
        elif block.header.prevhash in self.db:
            print(
                f'{self.node.address} at {self.env.now}: Receiving block #{block.header.number} ({block.header.hash[:8]}) not on head ({self._head_hash[:8]}), adding to secondary post state')
            self.consensus.apply_block(self.env, 2)
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
                    if b.prevhash not in self.db or self.db.get(
                            b.prevhash) == self.genesis.header.hash:
                        break
                    b = self.get_parent(b)
                replace_from = b.header.number
                # Replace block index and tx indices, and edit the state cache

                # Get a list of all accounts that have been edited along the old and
                # new chains
                changed_accts = {}
                # Read: for i in range(common ancestor block number...new block
                # number)
                for i in itertools.count(replace_from):
                    log.info('Rewriting height %d' % i)
                    key = b'block:%d' % i
                    # Delete data for old blocks
                    orig_at_height = self.db.get(
                        key) if key in self.db else None
                    if orig_at_height:
                        orig_block_at_height = self.get_block(orig_at_height)
                        log.info(
                            '%s no longer in main chain' %
                            encode_hex(
                                orig_block_at_height.header.hash))
                        # Delete from block index
                        self.db.delete(key)
                        # Delete from txindex
                        for tx in orig_block_at_height.transactions:
                            if b'txindex:' + tx.hash in self.db:
                                self.db.delete(b'txindex:' + tx.hash)
                        # Add to changed list
                        acct_list = self.db.get(
                            b'changed:' + orig_block_at_height.hash)
                        for j in range(0, len(acct_list), 20):
                            changed_accts[acct_list[j: j + 20]] = True
                    # Add data for new blocks
                    if i in new_chain:
                        new_block_at_height = new_chain[i]
                        log.info(
                            '%s now in main chain' %
                            encode_hex(
                                new_block_at_height.header.hash))
                        # Add to block index
                        self.db.put(key, new_block_at_height.header.hash)
                        # Add to txindex
                        for j, tx in enumerate(
                                new_block_at_height.transactions):
                            self.db.put(b'txindex:' + tx.hash,
                                        rlp.encode([new_block_at_height.number, j]))
                        # Add to changed list
                        if i < b.number:
                            acct_list = self.db.get(
                                b'changed:' + new_block_at_height.hash)
                            for j in range(0, len(acct_list), 20):
                                changed_accts[acct_list[j: j + 20]] = True
                    if i not in new_chain and not orig_at_height:
                        break
                # Add changed list from new head to changed list
                for c in changed.keys():
                    changed_accts[c] = True
                # Update the on-disk state cache
                for addr in changed_accts.keys():
                    data = temp_state.trie.get(addr)
                    if data:
                        self.state.db.put(b'address:' + addr, data)
                    else:
                        try:
                            self.state.db.delete(b'address:' + addr)
                        except KeyError:
                            pass
                self.head_hash = block.header.hash
                self.state = temp_state
                self.state.executing_on_head = True
        # Block has no parent yet
        else:
            if block.header.prevhash not in self.parent_queue:
                self.parent_queue[block.header.prevhash] = []
            self.parent_queue[block.header.prevhash].append(block)
            print(
                f'{self.node.address} at {self.env.now}: Got block #{block.header.number} ({block.header.hash[:8]}) with prevhash {block.header.prevhash[:8]}, parent not found. Delaying for now')
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
