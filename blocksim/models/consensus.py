from blocksim.utils import get_random_values


class Consensus:
    """ Defines the consensus model.

    The goal of this model is to simulate the rules that a node needs to follow to reach consensus
    between his peers.

    In order to simplify, we only take into account the duration of block and transaction validation,
    given by the user as simulation input.
    """

    def __init__(self, env):
        self.env = env

    def calc_difficulty(self, parent, timestamp):
        """Difficulty adjustment algorithm for the simulator.
        A block that is created in less time, have more difficulty associated"""
        timestamp_diff = timestamp - parent.header.timestamp
        return int(parent.header.difficulty + timestamp_diff)

    def validate_block(self, block=None):
        """ Simulates the block validation.
        For now, it only applies a delay in simulation, corresponding to previous measurements"""
        delay = round(get_random_values(
            self.env.delays['block_validation'])[0], 4)
        return delay

    def validate_transaction(self, tx=None):
        """ Simulates the transaction validation.
        For now, it only calculates a delay in simulation, corresponding to previous measurements"""
        delay = round(get_random_values(
            self.env.delays['tx_validation'])[0], 4)
        return delay
