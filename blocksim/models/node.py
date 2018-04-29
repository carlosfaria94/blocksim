from collections import namedtuple

from blocksim.models.network import Connection, Network
from blocksim.models.db import BaseDB
from blocksim.models.chain import Chain
from blocksim.models.ethereum.block import Block, BlockHeader
from blocksim.models.transaction_queue import TransactionQueue

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
    `location` and his `transmission_speed`.

    In order to a node to be identified in the network simulation, is needed to have an `address`
    """

    def __init__(self,
                 env,
                 network: Network,
                 transmission_speed,
                 download_rate,
                 upload_rate,
                 location: str,
                 address: str,
                 is_mining=False):
        self.env = env
        self.network = network
        self.transmission_speed = transmission_speed
        self.download_rate = download_rate
        self.upload_rate = upload_rate
        self.location = location
        self.address = address
        self.is_mining = is_mining
        self.active_sessions = {}
        # Transaction Queue to store the transactions
        # TODO: The transaction queue delay is hard coded
        self.transaction_queue = TransactionQueue(env, 2, self)
        # Create genesis block and init the chain
        genesis = Block(BlockHeader())
        # Create a database to this node
        db = BaseDB()
        self.chain = Chain(genesis, db)
        # Join the node to the network
        self.network.add_node(self)
        self.connecting = None

    def connect(self, upload_rate, *nodes):
        """Simulate an acknowledgement phase with given nodes"""
        for node in nodes:
            connection = Connection(self.env, self, node)
            self.active_sessions[node.address] = {
                'connection': connection,
                'knownTxs': {''},
                'knownBlocks': {''}
            }
            self.connecting = self.env.process(
                self._connecting(upload_rate, node, connection))

    def _connecting(self, upload_rate, node, connection):
        """Simulates the time needed to perform TCP handshake and acknowledgement phase"""
        # TODO: Calculate a delay/timeout do simulate the TCP handshake + HELLO ACK protocol
        # TODO: Message size?
        yield self.env.timeout(upload_rate)
        print('{} at {}: Connection established with {}'.format(
            self.address, self.env.now, node.address))
        # Start listening for messages from the destination node
        self.env.process(
            connection.destination_node.listening_node(connection))

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

    def _read_envelope(self, envelope, connection):
        print('{} at {}: Receive a message (ID: {}) created at {} from {}'.format(
            self.address,
            self.env.now,
            envelope.msg['id'],
            envelope.timestamp,
            envelope.origin.address
        ))

    def listening_node(self, connection):
        print('{} at {}: Listening for connections from the {}'
              .format(self.address, self.env.now, connection.origin_node.address))
        while True:
            # Get the messages from  connection
            envelope = yield connection.get()
            self._read_envelope(envelope, connection)
            yield self.env.timeout(self.download_rate)

    def send(self, destination_address: str, upload_rate, msg):
        node = self.active_sessions.get(destination_address)
        active_connection = node.get('connection')
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

        if upload_rate is None:
            upload_rate = self.upload_rate
        yield self.env.timeout(upload_rate)
        envelope = Envelope(
            msg, self.env.now, active_connection.destination_node, active_connection.origin_node)
        active_connection.put(envelope)

    def broadcast(self, upload_rate, msg):
        """Broadcast a message to all nodes with an active session"""
        # TODO: Add a Store here to queue the messages that need to be sent

        for node_address, node in self.active_sessions.items():
            connection = node.get('connection')

            if connection is None:
                raise RuntimeError('Not possible to create a direct connection with the node {}'
                                   .format(node_address))

            # TODO: Calculate a delay/timeout do simulate the TCP handshake ??
            yield self.env.timeout(3)
            # TODO: When sending add an upload rate
            if upload_rate is None:
                upload_rate = self.upload_rate
            yield self.env.timeout(upload_rate)
            envelope = Envelope(
                msg, self.env.now, connection.destination_node, connection.origin_node)
            connection.put(envelope)
