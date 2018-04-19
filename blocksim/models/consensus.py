""" Defines the consensus model.

The goal of this model is to define the rules that a node needs to follow to reach consensus
between his peers.

The information needed to process a transaction or a block is located within the state
itself, allowing the actual state transition logic to be a very clean `apply_transaction(state, tx)`
and `apply_block(state, block)`.
"""

null_address = b'\xff' * 20

def apply_block(state, block):
    """Applies the block-level state transition function"""
    pass


def apply_transaction(state, tx):
    """Applies the state transition function"""
    pass


def validate_transaction(env, duration, state, tx):
    """Validates the transaction.
    (1) the transaction is well-formed
    (2) the transaction signature is valid
    (3) the transaction nonce is valid (equivalent to the sender account’s current nonce)
    (4) the gas limit is no smaller than the intrinsic gas (21000), used by the transaction
    (5) the sender account balance contains at least the cost, required in up-front payment.
    """
    yield env.timeout(duration)
