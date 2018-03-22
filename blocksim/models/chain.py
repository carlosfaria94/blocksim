from blocksim.models.storage import Storage

class Chain:
    """ Defines the chain model."""

    _score = 0
    _best_hash = None
    _genesis_hash = None

    def __init__(self):
        self.storage = Storage
        # Total Difficulty of the best chain. Integer, as found in block header

    @property
    def score(self):
        # TODO: Score of the best chain. Integer, as found in block header.
        return self._score

    @property
    def best_hash(self):
        # TODO: The hash of the best (i.e. highest score) known block.
        return self._best_hash

    @property
    def genesis_hash(self):
        # TODO: Get the genesis hash
        return self._genesis_hash

    def get_parent(self, block):
        # GENESIS Block do not have parent
        if block.number == 0:
            return None
        return self.get_block(block.prevhash)

    def get_block(self, block_hash):
        return self.storage.get(block_hash)
