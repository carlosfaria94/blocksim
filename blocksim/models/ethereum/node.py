from blocksim.models.node import Node
from blocksim.models.network import Network, Connection
from blocksim.models.ethereum.message import Message
from blocksim.models.consensus import validate_transaction

class ETHNode(Node):
    def __init__(self,
                env,
                network: Network,
                transmission_speed,
                download_rate,
                upload_rate,
                location: str,
                address: str,
                is_mining=False):
        super().__init__(env,
                        network,
                        transmission_speed,
                        download_rate,
                        upload_rate,
                        location,
                        address,
                        is_mining)

    def handshake(self, network: str, total_difficulty: int, best_hash: str, genesis_hash: str):
        """Handshake executes the ETH protocol handshake, negotiating network, difficulties,
        head and genesis blocks"""
        # Get the difficulty from the head of the chain, known as Total Difficulty (TD)
        my_total_difficulty = self.chain.head.header.difficulty
        if my_total_difficulty < total_difficulty:
            print('I am not sync, I need to sync with this node')
        else:
            print('I am sync with this node')

    def get_node_status(self, node):
        status = Message(node).status()
        # TODO: Apply a deplay according to network communication between nodes
        yield self.env.timeout(3)
        return status

    def broadcast_transactions(self, transactions: list, upload_rate):
        """Broadcast transactions to all nodes with an active session and mark the hashes
        as known by each node"""
        yield self.connecting # Wait for all connections
        for node_address, node in self.active_sessions.items():
            for tx in transactions:
                # Checks if the transaction was previous sent
                if any({tx.hash} & node.get('knownTxs')):
                    print('{} at {}: Transaction {} was already sent to {}'.format(
                        self.address, self.env.now, tx.hash[:8], node_address))
                    transactions.remove(tx)
                else:
                    self._mark_transaction(tx.hash, node_address)

            # Only send if it has transactions
            if transactions:
                print('{} at {}: {} transactions ready to be sent'.format(
                    self.address, self.env.now, len(transactions)))
                transactions_msg = Message(self).transactions(transactions)

                #TODO: We need first know the status of the other node and then broadcast
                connection = node.get('connection')
                self.env.process(self.get_node_status(connection.destination_node))

                self.env.process(self.broadcast(upload_rate, transactions_msg))

    def send_status(self, destination_address: str, upload_rate):
        status_msg = Message(self).status()
        self.env.process(self.send(destination_address, upload_rate, status_msg))

    def _read_envelope(self, envelope, connection):
        super()._read_envelope(envelope, connection)
        if envelope.msg['id'] == 1:
            self._receive_status(envelope, connection)
        if envelope.msg['id'] == 2:
            self._receive_transactions(envelope, connection)

    def _receive_status(self, envelope, connection):
        pass

    def _receive_transactions(self, envelope, connection):
        """Handle transactions received"""
        # If node is miner store transactions in a pool (ordered by the gas price)
        transactions = envelope.msg.get('transactions')
        if self.is_mining:
            for tx in transactions:
                self.transaction_queue.put(tx)
        else:
            #TODO: validate_transaction('', tx)
            self.env.process(self.broadcast_transactions(transactions, None))

    def send_block_headers(self, request: dict, destination_address: str, upload_rate):
        """Send block headers for any node that request it, identified by the `destination_address`
        ```
        request = { 
            block_number,
            max_headers,
            reverse
        }
        ```
        """
        block_number = request.get('block_number', 0)
        max_headers = request.get('max_headers', 1)
        reverse = request.get('reverse', 1)

        block_hash = self.chain.get_blockhash_by_number(block_number)
        block_hashes = self.chain.get_blockhashes_from_hash(block_hash, max_headers)

        block_headers = []
        for _block_hash in block_hashes:
            block_header = self.chain.get_block(_block_hash).header
            block_headers.append(block_header)
        if reverse == 0:
            block_headers.reverse()

        block_headers_msg = Message(self).block_headers(block_headers)
        self.env.process(self.send(destination_address, upload_rate, block_headers_msg))

    def send_block_bodies(self, request: dict, destination_address: str, upload_rate):
        """Send block bodies for any node that request it, identified by the `destination_address`.

        In `request['hashes']` we obtain a list of hashes of block bodies being requested
        """
        hashes = request.get('hashes')

        block_bodies = []
        for block_hash in hashes:
            block = self.chain.get_block(block_hash)
            block_bodies.append(block)

        block_bodies_msg = Message(self).block_bodies(block_bodies)
        self.env.process(self.send(destination_address, upload_rate, block_bodies_msg))

    def request_headers(self,
                        block_number: int,
                        max_headers: int,
                        reverse: int,
                        destination_address: str,
                        upload_rate):
        """Request a node (identified by the `destination_address`) to return block headers.

        Request must contain a number of block headers, of rising number when `reverse` is `0`,
        falling when `1`, beginning at `block_number`.
        At most `max_headers` items.
        """
        get_block_headers_msg = Message(self).get_block_headers(block_number, max_headers, reverse)
        self.env.process(self.send(destination_address, upload_rate, get_block_headers_msg))

    def request_bodies(self, hashes: list, destination_address: str, upload_rate):
        """Request a node (identified by the `destination_address`) to return block bodies.
        Specify a list of `hashes` that we're interested in.
        """
        get_block_bodies_msg = Message(self).get_block_bodies(hashes)
        self.env.process(self.send(destination_address, upload_rate, get_block_bodies_msg))

