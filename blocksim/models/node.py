from collections import namedtuple

from models.network import Connection

Envelope = namedtuple('Envelope', 'msg, timestamp, size, destination, origin')

class Node:
    """This class represents the node"""
    def __init__(self, env, network, address, location, transmission_speed):
        self.env = env
        self.network = network
        self.transmission_speed = transmission_speed
        self.location = location
        self.address = address
        self.inbound_connections = dict()
        self.outbound_connections = dict()
        # The node will join to the network
        network.set_node(self)

    def get_inbound_connections(self, address):
        if not self.inbound_connections:
            raise RuntimeError('There are no inbound connections.')
        return self.inbound_connections(address)

    def set_inbound_connections(self, address, connection):
        self.inbound_connections[address] = connection

    def get_outbound_connections(self, address):
        if not self.outbound_connections:
            raise RuntimeError('There are no outbound connections.')
        return self.outbound_connections(address)

    def set_outbound_connections(self, address, connection):
        self.outbound_connections[address] = connection

    def send(self, destination_address, upload_rate, msg):
        """Sends a message to a specific `destination_address`"""
        # TODO: Add a Store here to queue the messages that need to be sent
        # TODO: When sending add an upload rate
        connection = self.outbound_connections.get(destination_address)
        print('CONNECTION {}'.format(connection))
        if connection is None:
            print('At {}: Node {} do not have an outbound connection with {}'
                .format(self.env.now, self.address, destination_address))
            # TODO: Calculate a delay/timeout do simulate the TCP handshake
            yield self.env.timeout(3)
            connection = self.init_connection(destination_address)
        yield self.env.timeout(upload_rate)
        envelope = Envelope(msg, self.env.now, 1, connection.destination_node, connection.origin_node)
        connection.put(envelope)

    def listening(self, connection, download_rate):
        # TODO: When sending add an download rate in Mbps
        print('At {}: Node {} is listening for inbound connections from the {}'
            .format(self.env.now, self.address, connection.destination_node.address))
        while True:
            # Get the message from connection
            envelope = yield connection.get()
            print('At {}: Node with address {} receive the message: {} at {} from {}'.format(
                self.env.now,
                self.address,
                envelope.msg,
                envelope.timestamp,
                envelope.origin.address
            ))

    def receive_connection(self, new_connection):
        """
        Node receives a new connection needs to be added to the inbound connections and
        start listening for messages
        """
        print('At {}: Node {} is receiving a new connection from Node {}'.format(
            self.env.now,
            self.address,
            new_connection.origin_node.address
        ))
        self.set_inbound_connections(new_connection.origin_node.address, new_connection)
        self.env.process(self.listening(new_connection, 1))

    def init_connection(self, destination_address):
        """
        Initiate a connection to the node with `destination_address`, 
        by creating a new `connection` 
        
        """
        print('At {}: Node {} is initiating a connection with {}'.format(
            self.env.now,
            self.address,
            destination_address
        ))
        destination_node = self.network.get_node(destination_address)
        if destination_node is None:
            raise RuntimeError('The node you are trying to connect it is not reachable')
        
        new_connection = Connection(self.env, self, destination_node)
        
        destination_node.receive_connection(new_connection)

        self.set_outbound_connections(destination_address, new_connection)
        return new_connection