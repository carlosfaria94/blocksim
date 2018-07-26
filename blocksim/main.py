import time
from blocksim.world import SimulationWorld
from blocksim.node_factory import NodeFactory
from blocksim.models.network import Network
from blocksim.models.transaction import Transaction


def generate_transactions(n):
    return [Transaction(
        'address', 'address', 140, f'sig{i}', 50) for i in range(n)]


def set_simulation():
    now = int(time.time())
    # TODO: Create a func to user input only days and converts to seconds
    duration = now + 10000
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
            'how_many': 2,
            'mega_hashrate_range': "(20, 40)"
        },
        'Ireland': {
            'how_many': 1,
            'mega_hashrate_range': "(20, 40)"
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
    # Create all nodes
    nodes_list = factory.create_nodes(miners, non_miners)
    # Start the network heartbeat
    world.env.process(network.start_heartbeat())
    # Full Connect all nodes
    for node in nodes_list:
        node.connect(nodes_list)

    transactions = generate_transactions(6)

    world.env.process(nodes_list[2].broadcast_transactions(transactions))

    world.start_simulation()


if __name__ == '__main__':
    set_simulation()
