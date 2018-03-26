""" Defines the consensus model.

The goal of this model is to define the rules that a node needs to follow to reach consensus
between his peers.

The information needed to process a transaction or a block is located within the state
itself, allowing the actual state transition logic to be a very clean `apply_transaction(state, tx)`
and `apply_block(state, block)`.
"""

def apply_block(state, block):
    """Applies the block-level state transition function"""
    print('apply block', state, block)


def apply_transaction(state, tx):
    """Applies the state transition function"""
    print('apply STF', state, tx)
