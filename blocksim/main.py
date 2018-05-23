import simpy

from blocksim.models.network import Network
from blocksim.models.ethereum.node import ETHNode
from blocksim.models.ethereum.transaction import ETHTransaction
from blocksim.models.ethereum.block import Block, BlockHeader

SIM_DURATION = 1000
ENV = simpy.Environment()


def create_random_tx(how_many):
    pass
    # return [Transaction(1, 20, 100, 'lisbon-address', 100) for i in range(how_many)]


def create_random_blocks(how_many):
    genesis_block = Block(BlockHeader(), create_random_tx(20))
    blocks = [genesis_block]
    for i in range(how_many):
        block = Block(BlockHeader())
    return blocks


def run_simulation(env):
    """ Setup and start the simulation """
    # Create the network
    network = Network(env, 'NetworkXPTO')

    node_lisbon = ETHNode(env, network, 1, 2, 3,
                          'Lisbon', 'lisbon-address', True)
    node_lisbon2 = ETHNode(env, network, 1, 2, 3,
                           'Lisbon', 'lisbon2-address', True)
    node_berlin = ETHNode(env, network, 1, 2, 3, 'Berlin', 'berlin-address')

    node_berlin.connect(5, node_lisbon)
    node_berlin.connect(2, node_lisbon2)
    node_lisbon2.connect(3, node_berlin)
    node_lisbon.connect(6, node_berlin)

    first_tx = ETHTransaction(
        'lisbon-address', 'berlin-address', 140, 'sig1', 1, 50, 100)
    second_tx = ETHTransaction(
        'lisbon-address', 'berlin-address', 20, 'sig2', 2, 40, 10)
    third_tx = ETHTransaction(
        'lisbon-address', 'berlin-address', 1000, 'sig3', 3, 50, 50)
    transactions = [first_tx, second_tx, third_tx]

    env.process(node_berlin.broadcast_transactions(transactions, 2))

    env.run(until=SIM_DURATION)


if __name__ == '__main__':
    run_simulation(ENV)
