from blocksim.world import SimulationWorld
from blocksim.models.network import Network
from blocksim.models.bitcoin.node import BTCNode
from blocksim.models.transaction import Transaction
import numpy


def set_simulation():
    WORLD = SimulationWorld(10000, 0, 'bitcoin',
                            'measures-input/latency.json',
                            'measures-input/bandwidth.json',
                            {'name': 'ups', 'parameters': (1, 45, 5)},
                            {'name': 'ups', 'parameters': (1, 45, 5)},
                            {'name': 'ups', 'parameters': (1, 45, 5)})
    # run_model(WORLD)


def run_model(world):
    env = world.environment

    # Create the network
    network = Network(env, 'NetworkXPTO')

    node_lisbon = BTCNode(env, network, 1, 2, 3,
                          'Lisbon', 'lisbon', True)
    node_barcelona = BTCNode(env, network, 1, 2, 3,
                             'Barcelona', 'barcelona', True)
    node_berlin = BTCNode(env, network, 1, 2, 3, 'Berlin', 'berlin')

    node_berlin.connect(5, node_lisbon, node_barcelona)
    node_barcelona.connect(3, node_berlin, node_lisbon)
    node_lisbon.connect(6, node_berlin, node_barcelona)

    first_tx = Transaction(
        'lisbon-address', 'berlin-address', 140, 'sig1', 50)
    second_tx = Transaction(
        'lisbon-address', 'berlin-address', 20, 'sig2', 40)
    third_tx = Transaction(
        'lisbon-address', 'berlin-address', 1000, 'sig3', 10)
    transactions = [first_tx, second_tx, third_tx]

    env.process(node_berlin.broadcast_transactions(transactions, 2))

    world.start_simulation()


if __name__ == '__main__':
    set_simulation()
