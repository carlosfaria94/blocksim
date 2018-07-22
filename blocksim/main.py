from blocksim.world import SimulationWorld
from blocksim.node_factory import NodeFactory
from blocksim.models.network import Network
from blocksim.models.transaction import Transaction


def set_simulation():
    world = SimulationWorld(
        100000,
        0,
        'bitcoin',
        'measures-input/latency.json',
        'measures-input/download-bandwidth.json',
        'measures-input/upload-bandwidth.json',
        'measures-input/delays.json')
    run_model(world)


def run_model(world):
    # Create the network
    network = Network(world.env, 'NetworkXPTO')

    miners = {
        'Ohio': {
            'how_many': 1
        },
        'Ireland': {
            'how_many': 2
        }
    }
    non_miners = {
        'Ohio': {
            'how_many': 1
        },
        'Ireland': {
            'how_many': 2
        }
    }
    factory = NodeFactory(world, network)
    nodes = factory.create_nodes(miners, non_miners)

    first_tx = Transaction(
        'lisbon-address', 'berlin-address', 140, 'sig1', 50)
    second_tx = Transaction(
        'lisbon-address', 'berlin-address', 20, 'sig2', 40)
    third_tx = Transaction(
        'lisbon-address', 'berlin-address', 1000, 'sig3', 10)
    transactions = [first_tx, second_tx, third_tx]

    world.env.process(nodes[2].broadcast_transactions(transactions, 2))

    world.start_simulation()


if __name__ == '__main__':
    set_simulation()
