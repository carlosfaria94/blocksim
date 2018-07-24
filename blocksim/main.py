import time
from blocksim.world import SimulationWorld
from blocksim.node_factory import NodeFactory
from blocksim.models.network import Network
from blocksim.models.transaction import Transaction


def set_simulation():
    now = int(time.time())
    # TODO: Create a func to user input only days and converts to seconds
    duration = now + 100000
    world = SimulationWorld(
        duration,
        now,
        'bitcoin',
        'input-parameters/latency.json',
        'input-parameters/throughput-received.json',
        'input-parameters/throughput-sent.json',
        'input-parameters/delays.json')
    run_model(world)


def run_model(world):
    # Create the network
    network = Network(world.env, 'NetworkXPTO')

    miners = {
        'Ohio': {
            'how_many': 2
        },
        'Ireland': {
            'how_many': 1
        }
    }
    non_miners = {
        'Ohio': {
            'how_many': 2
        },
        'Ireland': {
            'how_many': 1
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

    world.env.process(nodes[2].broadcast_transactions(transactions))

    world.start_simulation()


if __name__ == '__main__':
    set_simulation()
