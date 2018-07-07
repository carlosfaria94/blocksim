from blocksim.models.consensus import Consensus
from blocksim.models.ethereum.config import default_config


class ETHConsensus(Consensus):
    """ Defines the Ethereum consensus model.

    The goal of this model is to simulate the rules that a node needs to follow to reach consensus
    between his peers.

    In order to simplify, we only take into account the duration of block and transaction validation,
    given by the user as simulation input.
    """

    def __init__(self, env):
        super().__init__(env)
        self.config = default_config

    def calc_difficulty(self, parent, timestamp):
        """Difficulty adjustment algorithm for the simulator.
        A block that is created in less time, have more difficulty associated"""
        offset = parent.header.difficulty // self.config['BLOCK_DIFF_FACTOR']
        timestamp_diff = timestamp - parent.header.timestamp
        new_diff = int(parent.header.difficulty + offset - timestamp_diff)
        return new_diff
