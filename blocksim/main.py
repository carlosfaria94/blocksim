import time
import string
from random import randint, choices
from blocksim.world import SimulationWorld
from blocksim.node_factory import NodeFactory
from blocksim.models.network import Network
from blocksim.models.transaction import Transaction


def broadcast_transactions(world, number_of_batches, transactions_per_batch, interval, nodes_list):
    for i in range(number_of_batches):
        transactions = []
        for i in range(transactions_per_batch):
            # Generate a random string to a transaction be distinct from others
            rand_sign = ''.join(
                choices(string.ascii_letters + string.digits, k=20))
            tx = Transaction('address', 'address', 140, rand_sign, 50)
            transactions.append(tx)

        world.env.data['broadcast_transactions'] += len(transactions)
        # Choose a random node to broadcast the transaction
        world.env.process(
            nodes_list[randint(0, len(nodes_list)-1)].broadcast_transactions(transactions))
        yield world.env.timeout(interval)


def set_monitor(world):
    world.env.data = dict(
        number_of_transactions_queue=0,
        broadcast_transactions=0
    )


def set_simulation():
    now = int(time.time())
    # TODO: Create a func to user input only days and converts to seconds
    duration = now + 86400  # 1day
    world = SimulationWorld(
        duration,
        now,
        'input-parameters/config.json',
        'input-parameters/latency.json',
        'input-parameters/throughput-received.json',
        'input-parameters/throughput-sent.json',
        'input-parameters/delays.json')
    run_model(world)


def run_model(world):
    # Create the network
    network = Network(world.env, 'NetworkXPTO')
    set_monitor(world)
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

    world.env.process(broadcast_transactions(world, 5, 6, 300, nodes_list))

    world.start_simulation()

    print(world.env.data)


if __name__ == '__main__':
    set_simulation()
