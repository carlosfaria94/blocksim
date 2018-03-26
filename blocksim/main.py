import simpy

from blocksim.models.node import Node
from blocksim.models.network import Network
from blocksim.models.ethereum.block import BlockHeader
from blocksim.models.ethereum.messages import Messages

SIM_DURATION = 50
ENV = simpy.Environment()

def run_simulation(env):
    """ Setup and start the simulation """
    # Create the network
    network = Network(env)

    node_lisbon = Node(env, network, 'lisbon-address', 'Lisbon', 1)
    node_berlin = Node(env, network, 'berlin-address', 'Berlin', 1)

    print('---- messages ----')
    print(Messages(node_lisbon).hello())
    print(Messages(node_berlin).status())

    env.process(node_berlin.send('lisbon-address', 1, Messages(node_berlin).hello()))
    env.process(node_lisbon.send('berlin-address', 1, Messages(node_lisbon).hello()))

    env.process(node_berlin.send('lisbon-address', 1, Messages(node_berlin).status()))


    env.run(until=SIM_DURATION)

if __name__ == '__main__':
    run_simulation(ENV)
