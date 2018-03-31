import simpy

from blocksim.models.node import Node
from blocksim.models.network import Network
from blocksim.models.ethereum.block import BlockHeader
from blocksim.models.ethereum.node import ETHNode
from blocksim.models.ethereum.transaction import Transaction

SIM_DURATION = 50
ENV = simpy.Environment()

def run_simulation(env):
    """ Setup and start the simulation """
    # Create the network
    network = Network(env)

    node_lisbon = ETHNode(env, network, 1, 'Lisbon', 'lisbon-address')
    node_berlin = ETHNode(env, network, 1, 'Berlin', 'berlin-address')
    node_berlin.add_neighbors(node_lisbon)

    first_tx = Transaction(1, 100, 100, 'lisbon-address', 100)
    second_tx = Transaction(1, 100, 100, 'lisbon-address', 100)
    third_tx = Transaction(1, 100, 100, 'lisbon-address', 100)
    transactions = [first_tx, second_tx, third_tx]

    node_berlin.send_transactions(transactions, 'lisbon-address', 2)

    env.run(until=SIM_DURATION)

if __name__ == '__main__':
    run_simulation(ENV)
