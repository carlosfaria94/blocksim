from collections import namedtuple
from blocksim.models.network import Connection, Network
from blocksim.models.chain import Chain
from blocksim.models.consensus import Consensus
from blocksim.utils import get_received_delay, get_sent_delay, get_latency_delay, time

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
                 chain: Chain,
                 consensus: Consensus):
        self.env = env
        self.network = network
        self.location = location
        self.address = address
        self.chain = chain
        self.consensus = consensus
        self.active_sessions = {}
        self.connecting = None
        # Join the node to the network
        self.network.add_node(self)
        # Set the monitor to count the forks during the simulation
        key = f'forks_{address}'
        self.env.data[key] = 0

    def connect(self, nodes: list):
        """Simulate an acknowledgement phase with given nodes. During simulation the nodes
        will have an active session."""
        for node in nodes:
            # Ignore when a node is trying to connect to itself
            if node.address != self.address:
                connection = Connection(self.env, self, node)

                # Set the bases to monitor the block & TX propagation
                self.env.data['block_propagation'].update({
                    f'{self.address}_{node.address}': {}})
                self.env.data['tx_propagation'].update({
                    f'{self.address}_{node.address}': {}})

                self.active_sessions[node.address] = {
                    'connection': connection,
                    'knownTxs': {''},
                    'knownBlocks': {''}
                }
                self.connecting = self.env.process(
                    self._connecting(node, connection))

    def _connecting(self, node, connection):
        """Simulates the time needed to perform TCP handshake and acknowledgement phase.
        During the simulation we do not need to simulate it again.

        We consider that a node communicate with his peer using an open connection/channel
        during all the simulation."""
        origin_node = connection.origin_node
        destination_node = connection.destination_node
        latency = get_latency_delay(
            self.env, origin_node.location, destination_node.location)
        tcp_handshake_delay = 3*latency
        yield self.env.timeout(tcp_handshake_delay)
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
            f'{self.address} at {time(self.env)}: Receive a message (ID: {envelope.msg["id"]}) created at {envelope.timestamp} from {envelope.origin.address}')

    def listening_node(self, connection):
        while True:
            # Get the messages from  connection
            envelope = yield connection.get()
            origin_loc = envelope.origin.location
            dest_loc = envelope.destination.location
            message_size = envelope.msg['size']
            received_delay = get_received_delay(
                self.env, message_size, origin_loc, dest_loc)
            yield self.env.timeout(received_delay)

            # Monitor the transaction propagation on Ethereum
            if envelope.msg['id'] == 'transactions':
                tx_propagation = self.env.data['tx_propagation'][
                    f'{envelope.origin.address}_{envelope.destination.address}']
                txs = {}
                for tx in envelope.msg['transactions']:
                    initial_time = tx_propagation.get(tx.hash[:8], None)
                    if initial_time is not None:
                        propagation_time = self.env.now - initial_time
                        txs.update({f'{tx.hash[:8]}': propagation_time})
                self.env.data['tx_propagation'][f'{envelope.origin.address}_{envelope.destination.address}'].update(
                    txs)
            # Monitor the block propagation on Ethereum
            if envelope.msg['id'] == 'block_bodies':
                block_propagation = self.env.data['block_propagation'][
                    f'{envelope.origin.address}_{envelope.destination.address}']
                blocks = {}
                for block_hash, _ in envelope.msg['block_bodies'].items():
                    initial_time = block_propagation.get(block_hash[:8], None)
                    if initial_time is not None:
                        propagation_time = self.env.now - initial_time
                        blocks.update({f'{block_hash[:8]}': propagation_time})
                self.env.data['block_propagation'][f'{envelope.origin.address}_{envelope.destination.address}'].update(
                    blocks)

            self._read_envelope(envelope)

    def send(self, destination_address: str, msg):
        if self.address == destination_address:
            return
        node = self.active_sessions[destination_address]
        active_connection = node['connection']
        origin_node = active_connection.origin_node
        destination_node = active_connection.destination_node

        # Perform block validation before sending
        # For Ethereum it performs validation when receives the header:
        if msg['id'] == 'block_headers':
            for header in msg['block_headers']:
                delay = self.consensus.validate_block()
                yield self.env.timeout(delay)
        # For Bitcoin it performs validation when receives the full block:
        if msg['id'] == 'block':
            delay = self.consensus.validate_block()
            yield self.env.timeout(delay)
        # Perform transaction validation before sending
        # For Ethereum:
        if msg['id'] == 'transactions':
            for tx in msg['transactions']:
                delay = self.consensus.validate_transaction()
                yield self.env.timeout(delay)
        # For Bitcoin:
        if msg['id'] == 'tx':
            delay = self.consensus.validate_transaction()
            yield self.env.timeout(delay)

        upload_transmission_delay = get_sent_delay(
            self.env, msg['size'], origin_node.location, destination_node.location)
        yield self.env.timeout(upload_transmission_delay)

        envelope = Envelope(msg, time(self.env), destination_node, origin_node)
        active_connection.put(envelope)

    def broadcast(self, msg):
        """Broadcast a message to all nodes with an active session"""
        for add, node in self.active_sessions.items():
            connection = node['connection']
            origin_node = connection.origin_node
            destination_node = connection.destination_node

            # Monitor the transaction propagation on Ethereum
            if msg['id'] == 'transactions':
                txs = {}
                for tx in msg['transactions']:
                    txs.update({f'{tx.hash[:8]}': self.env.now})
                self.env.data['tx_propagation'][f'{origin_node.address}_{destination_node.address}'].update(
                    txs)
            # Monitor the block propagation on Ethereum
            if msg['id'] == 'new_blocks':
                blocks = {}
                for block_hash in msg['new_blocks']:
                    blocks.update({f'{block_hash[:8]}': self.env.now})
                self.env.data['block_propagation'][f'{origin_node.address}_{destination_node.address}'].update(
                    blocks)

            upload_transmission_delay = get_sent_delay(
                self.env, msg['size'], origin_node.location, destination_node.location)
            yield self.env.timeout(upload_transmission_delay)
            envelope = Envelope(msg, time(self.env),
                                destination_node, origin_node)
            connection.put(envelope)
