from blocksim.models.node import Node
from blocksim.models.network import Network, Connection
from blocksim.models.ethereum.block import Block, BlockHeader
from blocksim.models.ethereum.message import Message
from blocksim.models.consensus import validate_transaction
from blocksim.models.ethereum.config import default_config

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
        self.temp_headers = {}

    def init_mining(self,
                    duration_to_validate_tx,
                    duration_to_solve_puzzle,
                    gas_limit_per_block=default_config['GENESIS_GAS_LIMIT']):
        """Simulates the mining operation.
        (1) Gets transactions from the queue
        (2) Validates each transaction
        (3) Constructs a candidate block with intrinsic valid transactions
        (4) Solves a cryptographic puzzle
        (5) Broadcast the candidate block with the Proof of Work
        """
        print('{} at {}: Start mining process, waiting for transactions.'.format(
            self.address, self.env.now))
        while True:
            txs_intrinsic_gas = 0
            pending_txs = []
            while txs_intrinsic_gas < gas_limit_per_block:
                pending_tx = yield self.transaction_queue.get()
                pending_txs.append(pending_tx)
                txs_intrinsic_gas += pending_tx.startgas
            for pending_tx in pending_txs:
                # Simulate the transaction validation
                yield self.env.timeout(duration_to_validate_tx)

            # Build the candidate block
            candidate_block = self._build_candidate_block(
                gas_limit_per_block,
                txs_intrinsic_gas,
                pending_txs)
            print(f'{self.address} at {self.env.now}: New candidate block created {candidate_block.header.hash[:16]}')

            # Mine the block by simulating the resolution of a puzzle
            candidate_block = self._mine(candidate_block)
            yield self.env.timeout(duration_to_solve_puzzle)

            print(f'{self.address} at {self.env.now}: Solved the cryptographic puzzle for the candidate block {candidate_block.header.hash[:16]}')

            # Add the candidate block to the chain of the miner node
            self.chain.add_block(candidate_block)

            # We need to broadcast the new candidate block across the network
            self.send_new_blocks([candidate_block], None)

    def _mine(self, candidate_block):
        """Simulates the mining operation. Only change the nonce to 'MINED'
        In a simulation it is not needed to determine the nonce"""
        candidate_block.header.nonce = 'MINED'
        return candidate_block

    def _build_candidate_block(self, gas_limit_per_block, txs_intrinsic_gas, pending_txs):
        # Get the current head block
        prev_block = self.chain.head

        # TODO
        tx_list_root = uncles_hash = state_root = receipts_root = default_config['BLANK_ROOT']
        # TODO: Miner coinbase address
        coinbase = default_config['GENESIS_COINBASE']
        # TODO: Mining difficulty
        difficulty = default_config['GENESIS_DIFFICULTY']

        gas_used = txs_intrinsic_gas
        nonce = ''

        block_number = prev_block.header.number + 1
        timestamp = self.env.now
        candidate_block_header = BlockHeader(
            prev_block.header.hash,
            tx_list_root,
            block_number,
            timestamp,
            uncles_hash,
            state_root,
            receipts_root,
            coinbase,
            difficulty,
            gas_limit_per_block,
            txs_intrinsic_gas,
            nonce)
        return Block(candidate_block_header, pending_txs)

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
        if envelope.msg['id'] == 0: # status
            self._receive_status(envelope, connection)
        if envelope.msg['id'] == 1: # new_blocks
            self._receive_new_blocks(envelope, connection)
        if envelope.msg['id'] == 2: # transactions
            self._receive_transactions(envelope, connection)
        if envelope.msg['id'] == 3: # get_block_headers
            self.send_block_headers(envelope.msg, envelope.origin.address)
        if envelope.msg['id'] == 4: # block_headers
            self._receive_block_headers(envelope, connection)
        if envelope.msg['id'] == 5: # get_block_bodies
            self.send_block_bodies(envelope.msg, envelope.origin.address)
        if envelope.msg['id'] == 6: # block_bodies
            self._receive_block_bodies(envelope, connection)

    def _receive_status(self, envelope, connection):
        pass

    def _receive_new_blocks(self, envelope, connection):
        """Handle new blocks received.
        The destination only receives the hash and number of the block. It is needed to
        ask for the header and body."""
        new_blocks = envelope.msg['new_blocks']
        print('{} at {}: New blocks received {}'.format(
            self.address, self.env.now, new_blocks))
        lowest_block_number = min(block_number for _, block_number in new_blocks.items())
        self.request_headers(lowest_block_number, len(new_blocks), 0, envelope.origin.address)

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

    def _receive_block_headers(self, envelope, connection):
        """Handle block headers received"""
        block_headers = envelope.msg.get('block_headers')
        # Save the header in a temporary list
        hashes = []
        for header in block_headers:
            self.temp_headers[header.hash] = header
            hashes.append(header.hash)
        self.request_bodies(hashes, envelope.origin.address)

    def _receive_block_bodies(self, envelope, connection):
        """Handle block bodies received
        Assemble the block header in a temporary list with the block body received and
        insert it in the blockchain"""
        block_bodies = envelope.msg.get('block_bodies')
        for block_hash, block_txs in block_bodies.items():
            if block_hash in self.temp_headers:
                header = self.temp_headers.get(block_hash)
                new_block = Block(header, block_txs)
                self.chain.add_block(new_block)
                del self.temp_headers[block_hash]
        print(f'{self.address} at {self.env.now}: {len(block_bodies)} Block(s) assembled and added to the blockchain')

    def send_new_blocks(self, new_blocks, upload_rate):
        """Specify one or more new blocks which have appeared on the network.
        To be maximally helpful, nodes should inform peers of all blocks that
        they may not be aware of."""
        _new_blocks = {}
        for block in new_blocks:
            _new_blocks[block.header.hash] = block.header.number

        new_blocks_msg = Message(self).new_blocks(_new_blocks)
        self.env.process(self.broadcast(upload_rate, new_blocks_msg))

    def send_block_headers(self, request: dict, destination_address: str, upload_rate=None):
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
        print(f'{self.address} at {self.env.now}: {max_headers} Block header(s) preapred to send')

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

    def send_block_bodies(self, request: dict, destination_address: str, upload_rate=None):
        """Send block bodies for any node that request it, identified by the `destination_address`.

        In `request['hashes']` we obtain a list of hashes of block bodies being requested

        For now it only contains the transactions
        """
        hashes = request.get('hashes')

        block_bodies = {}
        for block_hash in hashes:
            block = self.chain.get_block(block_hash)
            block_bodies[block.header.hash] = block.transactions

        print(f'{self.address} at {self.env.now}: {len(block_bodies)} Block bodies(s) preapred to send')

        block_bodies_msg = Message(self).block_bodies(block_bodies)
        self.env.process(self.send(destination_address, upload_rate, block_bodies_msg))

    def request_headers(self,
                        block_number: int,
                        max_headers: int,
                        reverse: int,
                        destination_address: str,
                        upload_rate=None):
        """Request a node (identified by the `destination_address`) to return block headers.

        Request must contain a number of block headers, of rising number when `reverse` is `0`,
        falling when `1`, beginning at `block_number`.
        At most `max_headers` items.
        """
        get_block_headers_msg = Message(self).get_block_headers(block_number, max_headers, reverse)
        self.env.process(self.send(destination_address, upload_rate, get_block_headers_msg))

    def request_bodies(self, hashes: list, destination_address: str, upload_rate=None):
        """Request a node (identified by the `destination_address`) to return block bodies.
        Specify a list of `hashes` that we're interested in.
        """
        get_block_bodies_msg = Message(self).get_block_bodies(hashes)
        self.env.process(self.send(destination_address, upload_rate, get_block_bodies_msg))

