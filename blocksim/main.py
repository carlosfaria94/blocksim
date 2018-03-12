import simpy

from blocksim.models.node import Node
from blocksim.models.network import Network

SIM_DURATION = 50

def delay(env):
    yield env.timeout(3)

# Setup and start the simulation
print('Network Simulation')
env = simpy.Environment()

# I create the network
network = Network(env)

node_lisbon = Node(env, network, 'lisbon-address', 'Lisbon', 1)
node_berlin = Node(env, network, 'berlin-address', 'Berlin', 1)

print('Nodes in the network:')
for node in network.nodes:
    print(node)

env.process(node_berlin.send('lisbon-address', 5, 'HELLO LISBON'))
env.process(delay(env))
env.process(node_berlin.send('lisbon-address', 1, 'HELLO AGAIN LISBON'))
# env.process(node_lisbon.send('berlin-address', 1, 'HELLO BERLIN'))


env.run(until=SIM_DURATION)