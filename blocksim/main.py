import simpy

from blocksim.models.network import Network
from blocksim.models.ethereum.node import ETHNode
from blocksim.models.ethereum.transaction import ETHTransaction
from blocksim.models.ethereum.block import Block, BlockHeader

SIM_DURATION = 10000
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


def set_delays(env):
    env.delays = dict(
        VALIDATE_TX=2,
        TIME_BETWEEN_BLOCKS=100
    )
    print(env.delays)
    return env


def run_simulation(env):
    """ Setup and start the simulation """

    env = set_delays(env)

    # Create the network
    network = Network(env, 'NetworkXPTO')

    node_lisbon = ETHNode(env, network, 1, 2, 3,
                          'Lisbon', 'lisbon', True)
    node_barcelona = ETHNode(env, network, 1, 2, 3,
                             'Barcelona', 'barcelona', True)
    node_berlin = ETHNode(env, network, 1, 2, 3, 'Berlin', 'berlin')

    node_berlin.connect(5, node_lisbon, node_barcelona)
    node_barcelona.connect(3, node_berlin, node_lisbon)
    node_lisbon.connect(6, node_berlin, node_barcelona)

    first_tx = ETHTransaction(
        'lisbon-address', 'berlin-address', 140, 'sig1', 1, 50)
    second_tx = ETHTransaction(
        'lisbon-address', 'berlin-address', 20, 'sig2', 2, 40)
    third_tx = ETHTransaction(
        'lisbon-address', 'berlin-address', 1000, 'sig3', 3, 50)
    transactions = [first_tx, second_tx, third_tx]

    env.process(node_berlin.broadcast_transactions(transactions, 2))

    env.run(until=SIM_DURATION)


if __name__ == '__main__':
    run_simulation(ENV)
