import simpy

from blocksim.models.node import Node
from blocksim.models.network import Network
from blocksim.models.block import Block

SIM_DURATION = 50
ENV = simpy.Environment()

def run_simulation(env):
    """ Setup and start the simulation """
    print('Network Simulation')
    # Create the network
    network = Network(env)

    block1 = Block('ups')
    block2 = Block()
    print(block1)
    print(repr(block1))
    print(block2)
    print(repr(block2))
    print('blocks are equal?', block1 == block2)

    node_lisbon = Node(env, network, 'lisbon-address', 'Lisbon', 1)
    node_berlin = Node(env, network, 'berlin-address', 'Berlin', 1)

    print('Nodes in the network:')
    for node in network.nodes:
        print(node)

    env.process(node_berlin.send('lisbon-address', 5, 'HELLO LISBON'))
    env.process(node_berlin.send('lisbon-address', 1, 'HELLO AGAIN LISBON'))
    env.process(node_lisbon.send('berlin-address', 1, 'HELLO BERLIN'))

    env.run(until=SIM_DURATION)

if __name__ == '__main__':
    run_simulation(ENV)
