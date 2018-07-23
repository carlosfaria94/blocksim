from collections import namedtuple
from blocksim.models.network import Connection, Network
from blocksim.models.chain import Chain
from blocksim.utils import get_transmission_delay

Envelope = namedtuple('Envelope', 'msg, timestamp, destination, origin')

# Maximum transactions hashes to keep in the known list (prevent DOS)
MAX_KNOWN_TXS = 30000
# Maximum block hashes to keep in the known list (prevent DOS)
MAX_KNOWN_BLOCKS = 1024


class Node:
    """This class represents the node.

    Each node has their own `chain`, and when a node is initiated its started with a clean chain.

    A node needs to be initiated with known nodes to run the simulation. For now there is
    not any mechanism to discover nodes.

    To properly stimulate a real world scenario, the node model needs to know the geographic
    `location`.

    In order to a node to be identified in the network simulation, is needed to have an `address`
    """

    def __init__(self,
                 env,
                 network: Network,
                 location: str,
                 address: str,
                 chain: Chain):
        self.env = env
        self.network = network
        self.location = location
        self.address = address
        self.chain = chain
        self.active_sessions = {}
        # Join the node to the network
        self.network.add_node(self)
        self.connecting = None

    def connect(self, nodes: list):
        """Simulate an acknowledgement phase with given nodes.
        During simulation the nodes will have an active session."""
        for node in nodes:
            # Ignore when a node is trying to connect to itself
            if node.address != self.address:
                connection = Connection(self.env, self, node)
                self.active_sessions[node.address] = {
                    'connection': connection,
                    'knownTxs': {''},
                    'knownBlocks': {''}
                }
                self.connecting = self.env.process(
                    self._connecting(node, connection))

    def _connecting(self, node, connection):
        """Simulates the time needed to perform TCP handshake and acknowledgement phase"""
        # TODO: Calculate a delay/timeout do simulate the TCP handshake + HELLO ACK protocol
        # yield self.env.timeout(2)
        origin_node = connection.origin_node
        destination_node = connection.destination_node
        # TODO: Message size? Should be the TCP handshake?
        upload_transmission_delay = get_transmission_delay(
            self.env, 1, False, origin_node.location, destination_node.location)
        yield self.env.timeout(upload_transmission_delay)
        # print(
        #    f'{self.address} at {self.env.now}: Connection established with {node.address}')
        # Start listening for messages from the destination node
        self.env.process(destination_node.listening_node(connection))

    def _mark_block(self, block_hash: str, node_address: str):
        """Marks a block as known for a specific node, ensuring that it will never be
        propagated again."""
        node = self.active_sessions.get(node_address)
        known_blocks = node.get('knownBlocks')
        while len(known_blocks) >= MAX_KNOWN_BLOCKS:
            known_blocks.pop()
        known_blocks.add(block_hash)
        node['knownBlocks'] = known_blocks
        self.active_sessions[node_address] = node

    def _mark_transaction(self, tx_hash: str, node_address: str):
        """Marks a transaction as known for a specific node, ensuring that it will never be
        propagated again."""
        node = self.active_sessions.get(node_address)
        known_txs = node.get('knownTxs')
        while len(known_txs) >= MAX_KNOWN_TXS:
            known_txs.pop()
        known_txs.add(tx_hash)
        node['knownTxs'] = known_txs
        self.active_sessions[node_address] = node

    def _read_envelope(self, envelope):
        print(
            f'{self.address} at {self.env.now}: Receive a message (ID: {envelope.msg["id"]}) created at {envelope.timestamp} from {envelope.origin.address}')

    def listening_node(self, connection):
        # print('{} at {}: Listening for connections from the {}'
        #      .format(self.address, self.env.now, connection.origin_node.address))
        while True:
            # Get the messages from  connection
            envelope = yield connection.get()
            origin_loc = envelope.origin.location
            dest_loc = envelope.destination.location
            message_size = envelope.msg['size']
            trans_delay_download = get_transmission_delay(
                self.env, message_size, True, origin_loc, dest_loc)
            yield self.env.timeout(trans_delay_download)
            self._read_envelope(envelope)

    def send(self, destination_address: str, upload_transmission_delay, msg):
        node = self.active_sessions.get(destination_address)
        active_connection = node.get('connection')
        if active_connection is None and msg['id'] == 0:
            # We do not have an active connection with the destination because its a ACK msg
            destination_node = self.network.get_node(destination_address)
            active_connection = Connection(self.env, self, destination_node)
            # TODO: Professor: Should I apply the delay for the TCP handshake?
            # yield self.env.timeout(3)
        elif active_connection is None and msg['id'] != 0:
            # We do not have a connection and the message is not an ACK
            raise RuntimeError(
                f'It is needed to initiate an ACK phase with {destination_address} before sending any other message')

        origin_node = active_connection.origin_node
        destination_node = active_connection.destination_node
        if upload_transmission_delay is None:
            upload_transmission_delay = get_transmission_delay(
                self.env, msg['size'], False, origin_node.location, destination_node.location)
        yield self.env.timeout(upload_transmission_delay)
        envelope = Envelope(msg, self.env.now, destination_node, origin_node)
        active_connection.put(envelope)

    def broadcast(self, upload_transmission_delay, msg):
        """Broadcast a message to all nodes with an active session"""
        for node_address, node in self.active_sessions.items():
            connection = node.get('connection')
            if connection is None:
                raise RuntimeError(
                    f'Not possible to create a direct connection with the node {node_address}')

            # TODO: Professor: Should I apply the delay for the TCP handshake?
            # yield self.env.timeout(3)
            origin_node = connection.origin_node
            destination_node = connection.destination_node
            if upload_transmission_delay is None:
                upload_transmission_delay = get_transmission_delay(
                    self.env, msg['size'], False, origin_node.location, destination_node.location)
            yield self.env.timeout(upload_transmission_delay)
            envelope = Envelope(msg, self.env.now,
                                destination_node, origin_node)
            connection.put(envelope)
