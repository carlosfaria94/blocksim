import time
import string
from json import dumps as dump_json
from random import randint, choices
from blocksim.world import SimulationWorld
from blocksim.node_factory import NodeFactory
from blocksim.models.network import Network
from blocksim.models.transaction import Transaction
from blocksim.models.ethereum.transaction import Transaction as ETHTransaction


def broadcast_transactions(world, number_of_batches, transactions_per_batch, interval, nodes_list):
    for i in range(number_of_batches):
        transactions = []
        for i in range(transactions_per_batch):
            # Generate a random string to a transaction be distinct from others
            rand_sign = ''.join(
                choices(string.ascii_letters + string.digits, k=20))
            if world.blockchain == 'bitcoin':
                tx = Transaction('address', 'address', 140, rand_sign, 50)
            elif world.blockchain == 'ethereum':
                # TODO: Get startgas from a user input
                tx = ETHTransaction('address', 'address',
                                    140, rand_sign, i, 2, 10)
            transactions.append(tx)
        world.env.data['created_transactions'] += len(transactions)
        # Choose a random node to broadcast the transaction
        world.env.process(
            nodes_list[randint(0, len(nodes_list)-1)].broadcast_transactions(transactions))
        yield world.env.timeout(interval)


def write_report(world):
    with open('output/report.json', 'w') as f:
        f.write(dump_json(world.env.data))


def report_node_chain(world, nodes_list):
    for node in nodes_list:
        head = node.chain.head
        chain_list = []
        num_blocks = 0
        for i in range(head.header.number):
            b = node.chain.get_block_by_number(i)
            chain_list.append(str(b.header))
            num_blocks += 1
        chain_list.append(str(head.header))
        key = f'{node.address}_chain'
        world.env.data[key] = {
            'head_block_hash': f'{head.header.hash[:8]} #{head.header.number}',
            'number_of_blocks': num_blocks,
            'chain_list': chain_list
        }


def set_simulation():
    now = int(time.time())
    # TODO: Create a func to user input only days and converts to seconds
    duration = 72000
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

    report_node_chain(world, nodes_list)
    write_report(world)


if __name__ == '__main__':
    set_simulation()
