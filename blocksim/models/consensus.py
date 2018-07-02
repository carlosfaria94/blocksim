class Consensus:
    """ Defines the consensus model.

    The goal of this model is to simulate the rules that a node needs to follow to reach consensus
    between his peers.

    In order to simplify, we only take into account the duration of block and transaction validation,
    given by the user as simulation input.
    """

    def __init__(self, env):
        self.env = env

    def apply_block(self, duration, state=None, block=None):
        """ Simulates the block-level state transition function.
        For now, it only applies a delay in simulation, corresponding to previous measurements"""
        yield self.env.timeout(duration)

    def validate_block(self, duration, state=None, block=None):
        """ Simulates the block validation.
        For now, it only applies a delay in simulation, corresponding to previous measurements"""
        yield self.env.timeout(duration)

    def apply_transaction(self, duration, state=None, tx=None):
        """ Simulates the transaction-level state transition function.
        For now, it only applies a delay in simulation, corresponding to previous measurements"""
        yield self.env.timeout(duration)

    def validate_transaction(self, duration, state=None, tx=None):
        """ Simulates the transaction validation.
        For now, it only applies a delay in simulation, corresponding to previous measurements"""
        yield self.env.timeout(duration)
