import simpy

from blocksim.models.network import Network
from blocksim.models.ethereum.node import ETHNode
from blocksim.models.ethereum.transaction import Transaction
from blocksim.models.ethereum.block import Block, BlockHeader

SIM_DURATION = 1000
ENV = simpy.Environment()

def create_random_tx(how_many):
    return [Transaction(1, 20, 100, 'lisbon-address', 100) for i in range(how_many)]

def create_random_blocks(how_many):
    genesis_block = Block(BlockHeader(), create_random_tx(20))
    blocks = [ genesis_block ]
    for i in range(how_many):
        block = Block(BlockHeader())
    return blocks

def run_simulation(env):
    """ Setup and start the simulation """
    # Create the network
    network = Network(env, 'NetworkXPTO')

    node_lisbon = ETHNode(env, network, 1, 2, 3, 'Lisbon', 'lisbon-address', True)
    env.process(node_lisbon.init_mining(2, 15, 63000))
    node_berlin = ETHNode(env, network, 1, 2, 3, 'Berlin', 'berlin-address')
    node_berlin.connect(5, node_lisbon)
    node_lisbon.connect(6, node_berlin)

    first_tx = Transaction(1, 140, 'lisbon-address', 100)
    second_tx = Transaction(1, 120, 'lisbon-address', 100)
    third_tx = Transaction(1, 150, 'lisbon-address', 100)
    transactions = [first_tx, second_tx, third_tx]

    env.process(node_berlin.broadcast_transactions(transactions, 2))

    #for block in create_random_blocks(10):
    #    print(block.header.hash)

    env.run(until=SIM_DURATION)

if __name__ == '__main__':
    run_simulation(ENV)
