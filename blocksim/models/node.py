from collections import namedtuple

from blocksim.models.network import Connection, Network
from blocksim.models.chain import Chain
from blocksim.models.ethereum.block import Block, BlockHeader

Envelope = namedtuple('Envelope', 'msg, timestamp, destination, origin')

MAX_KNOWN_TXS = 30000 # Maximum transactions hashes to keep in the known list (prevent DOS)
MAX_KNOWN_BLOCKS = 1024 # Maximum block hashes to keep in the known list (prevent DOS)

class Node:
    """This class represents the node.

    Each node has their own `chain`, and when a node is initiated its started with a clean chain.

    A node needs to be initiated with known `neighbors` to run the simulation. For now there is
    not any mechanism to discover neighbors.

    To properly stimulate a real world scenario, the node model needs to know the geographic
    `location` and his `transmission_speed`.

    In order to a node to be identified in the network simulation, is needed to have an `address`
    """
    def __init__(self,
                env,
                network: Network,
                transmission_speed,
                download_rate,
                location: str,
                address: str):
        self.env = env
        self.transmission_speed = transmission_speed
        self.download_rate = download_rate
        self.location = location
        self.address = address
        self.neighbors = {}
        self.active_sessions = {}
        # Create genesis block and init the chain
        genesis = Block(BlockHeader())
        self.chain = Chain(genesis)
        # The node will join to the network
        network.add_node(self)
        self.network = network

    def send_ack(self, destination_address: str, upload_rate):
        """First packet sent over the connection, and sent once by both sides.
        No other messages may be sent until a ACK is received.
        When a ACK message is sent a new connection is created with the `destination_address`
        """
        ack_msg = {
            'id': 0,
            'size': 10 # TODO: Measure the size message
        }
        self.env.process(self.send(destination_address, upload_rate, ack_msg))

    def receive_ack(self, origin_address: str, connection: Connection):
        self.active_sessions[origin_address] = connection

    def add_neighbors(self, *nodes):
        """Add nodes as neighbors"""
        for node in nodes:
            connection = Connection(self.env, self, node)
            self.neighbors[node.address] = {
                'network': node.network.name,
                'connection': connection,
                'genesisHash': node.chain.genesis.header.hash,
                'bestHash': node.chain.head.header.hash,
                'location': node.location,
                'address': node.address,
                'knownTxs': {''},
                'knownBlocks': {''}
            }
        # Start listening for messages from the neighbors
        self.env.process(self.listening_neighbors())

    def _update_neighbors(self, new_neighbor: dict):
        address = new_neighbor.get('address')
        self.neighbors[address] = new_neighbor

    def _get_neighbor(self, neighbor_address: str):
        neighbor = self.neighbors.get(neighbor_address)
        if neighbor is None:
            print('Neighbor {} not reachable by the {}'.format(neighbor_address, self.address))
            return None
        else:
            return neighbor

    def _mark_block(self, block_hash: str, neighbor_address: str):
        """Marks a block as known for the neighbor, ensuring that it will never be
        propagated to this particular neighbor."""
        neighbor = self._get_neighbor(neighbor_address)
        known_blocks = neighbor.get('knownBlocks')
        while len(known_blocks) >= MAX_KNOWN_BLOCKS:
            known_blocks.pop()
        known_blocks.add(block_hash)
        neighbor['knownBlocks'] = known_blocks
        self._update_neighbors(neighbor)

    def _mark_transaction(self, tx_hash: str, neighbor_address: str):
        """Marks a transaction as known for the neighbor, ensuring that it will never be
        propagated to this particular neighbor."""
        neighbor = self._get_neighbor(neighbor_address)
        known_txs = neighbor.get('knownTxs')
        while len(known_txs) >= MAX_KNOWN_TXS:
            known_txs.pop()
        known_txs.add(tx_hash)
        neighbor['knownTxs'] = known_txs
        self._update_neighbors(neighbor)

    def read_envelope(self, envelope):
        print('{} at {}: Receive a message (ID: {}) created at {} from {}'.format(
                self.address,
                self.env.now,
                envelope.msg['id'],
                envelope.timestamp,
                envelope.origin.address
            ))

    def listening_neighbors(self):
        # TODO: When receiving add an download rate in Mbps
        for neighbor_address, neighbor in self.neighbors.items():
            connection = neighbor.get('connection')
            if connection is None:
                raise RuntimeError('{} at {}: There is not a direct connection with the neighbor {}'
                .format(self.address, self.env.now, neighbor_address))
            print('{} at {}: Node {} is listening for connections from the {}'
            .format(self.address, self.env.now, self.address, connection.destination_node.address))
            while True:
                # Get the messages from  connection
                envelope = yield connection.get()
                self.read_envelope(envelope)
                yield self.env.timeout(self.download_rate)

    def listening_node(self, connection):
        print('{} at {}: Node {} is listening for connections from the {}'
            .format(self.address, self.env.now, self.address, connection.destination_node.address))
        while True:
            # Get the messages from  connection
            envelope = yield connection.get()
            self.read_envelope(envelope)
            yield self.env.timeout(self.download_rate)

    def send(self, destination_address: str, upload_rate, msg):
        active_connection = self.active_sessions.get(destination_address)
        if active_connection is None and msg['id'] == 0:
            # We do not have an active connection with the destination because its a ACK msg
            destination_node = self.network.get_node(destination_address)
            active_connection = Connection(self.env, self, destination_node)
            # TODO: Calculate a delay/timeout do simulate the TCP handshake
            yield self.env.timeout(3)
        elif active_connection is None and msg['id'] != 0:
            # We do not have a connection and the message is not an ACK
            raise RuntimeError('It is needed to initiate an ACK phase with {} before sending any other message'
                    .format(destination_address))

        # The connection exist
        # The destination node need to start listening on this connection
        self.env.process(destination_node.listening_node(active_connection))
        yield self.env.timeout(upload_rate)
        envelope = Envelope(msg, self.env.now, active_connection.destination_node, active_connection.origin_node)
        active_connection.put(envelope)

    def broadcast_to_neighbors(self, upload_rate, msg):
        """Broadcast a message to all neighbors"""
        # TODO: Add a Store here to queue the messages that need to be sent

        for neighbor_address, neighbor in self.neighbors.items():
            connection = neighbor.get('connection')

            if connection is None:
                raise RuntimeError('Not possible to create a direct connection with the neighbor {}'
                    .format(neighbor_address))

            # TODO: Calculate a delay/timeout do simulate the TCP handshake ??
            yield self.env.timeout(3)
            # TODO: When sending add an upload rate
            yield self.env.timeout(upload_rate)
            envelope = Envelope(msg, self.env.now, connection.destination_node, connection.origin_node)
            connection.put(envelope)
