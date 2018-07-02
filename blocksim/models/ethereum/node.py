from blocksim.models.node import Node
from blocksim.models.network import Network
from blocksim.models.ethereum.block import Block, BlockHeader
from blocksim.models.ethereum.message import Message
from blocksim.models.chain import Chain
from blocksim.models.consensus import validate_transaction
from blocksim.models.db import BaseDB
from blocksim.models.transaction_queue import TransactionQueue
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
        # Create the Ethereum genesis block and init the chain
        genesis = Block(BlockHeader())
        chain = Chain(env, genesis, BaseDB())
        super().__init__(env,
                         network,
                         transmission_speed,
                         download_rate,
                         upload_rate,
                         location,
                         address,
                         chain)
        self.is_mining = is_mining
        self.temp_headers = {}
        if is_mining:
            # Transaction Queue to store the transactions
            # TODO: The transaction queue delay is hard coded
            self.transaction_queue = TransactionQueue(env, 2, self)
            # TODO: The mining delays hard coded
            env.process(self._init_mining(2, 15, 63000))
        self.network_message = Message(self)
        self.handshaking = env.event()

    def _init_mining(self,
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
        if self.is_mining is False:
            raise RuntimeError(f'Node {self.location} is not a miner')

        print(
            f'{self.address} at {self.env.now}: Start mining process, waiting for transactions.')
        while True:
            txs_intrinsic_gas = 0
            pending_txs = []
            while txs_intrinsic_gas < gas_limit_per_block:
                pending_tx = yield self.transaction_queue.get()
                pending_txs.append(pending_tx)
                txs_intrinsic_gas += pending_tx.startgas
                # Simulate the transaction validation
                validate_transaction(self.env, duration_to_validate_tx)

            # Build the candidate block
            candidate_block = self._build_candidate_block(
                gas_limit_per_block,
                txs_intrinsic_gas,
                pending_txs)
            print(
                f'{self.address} at {self.env.now}: New candidate block created {candidate_block.header.hash[:16]}')

            # Mine the block by simulating the resolution of a puzzle
            candidate_block = self._mine(candidate_block)
            yield self.env.timeout(duration_to_solve_puzzle)

            print(
                f'{self.address} at {self.env.now}: Solved the cryptographic puzzle for the candidate block {candidate_block.header.hash[:16]}')

            # Add the candidate block to the chain of the miner node
            self.chain.add_block(candidate_block)

            # We need to broadcast the new candidate block across the network
            self.broadcast_new_blocks([candidate_block], None)

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

    def connect(self, upload_rate, *nodes):
        super().connect(upload_rate, *nodes)
        for node in nodes:
            self._handshake(node.address, upload_rate)

    def _handshake(self, destination_address: str, upload_rate):
        """Handshake inform a node of its current ethereum state, negotiating network, difficulties,
        head and genesis blocks
        This message should be sent after the initial handshake and prior to any ethereum related messages."""
        status_msg = self.network_message.status()
        print(
            f'{self.address} at {self.env.now}: Status message sent to {destination_address}')
        self.env.process(
            self.send(destination_address, upload_rate, status_msg))

    def _receive_status(self, envelope):
        print(
            f'{self.address} at {self.env.now}: Receive status from {envelope.origin.address}')
        node = self.active_sessions.get(envelope.origin.address)
        node['status'] = envelope.msg
        self.active_sessions[envelope.origin.address] = node
        self.handshaking.succeed()
        self.handshaking = self.env.event()

    def broadcast_transactions(self, transactions: list, upload_rate):
        """Broadcast transactions to all nodes with an active session and mark the hashes
        as known by each node"""
        yield self.connecting  # Wait for all connections        print('test')
        yield self.handshaking  # Wait for handshaking to be completed
        for node_address, node in self.active_sessions.items():
            for tx in transactions:
                # Checks if the transaction was previous sent
                if any({tx.hash} & node.get('knownTxs')):
                    print(
                        f'{self.address} at {self.env.now}: Transaction {tx.hash[:8]} was already sent to {node_address}')
                    transactions.remove(tx)
                else:
                    self._mark_transaction(tx.hash, node_address)

        # Only send if it has transactions
        if transactions:
            print(
                f'{self.address} at {self.env.now}: {len(transactions)} transactions ready to be sent')
            transactions_msg = self.network_message.transactions(transactions)

            # TODO: We need first know the status of the other node and then broadcast
            #connection = node.get('connection')
            # self.env.process(self.get_node_status(
            #    connection.destination_node))

            self.env.process(self.broadcast(upload_rate, transactions_msg))

    def _read_envelope(self, envelope):
        super()._read_envelope(envelope)
        if envelope.msg['id'] == 'status':
            self._receive_status(envelope)
        if envelope.msg['id'] == 'new_blocks':
            self._receive_new_blocks(envelope)
        if envelope.msg['id'] == 'transactions':
            self._receive_transactions(envelope)
        if envelope.msg['id'] == 'get_headers':
            self._send_block_headers(envelope)
        if envelope.msg['id'] == 'block_headers':
            self._receive_block_headers(envelope)
        if envelope.msg['id'] == 'get_block_bodies':
            self._send_block_bodies(envelope)
        if envelope.msg['id'] == 'block_bodies':
            self._receive_block_bodies(envelope)

    def _receive_new_blocks(self, envelope):
        """Handle new blocks received.
        The destination only receives the hash and number of the block. It is needed to
        ask for the header and body."""
        new_blocks = envelope.msg['new_blocks']
        print(f'{self.address} at {self.env.now}: New blocks received {new_blocks}')
        lowest_block_number = min(
            block_number for _, block_number in new_blocks.items())
        self.request_headers(
            lowest_block_number, len(new_blocks), 0, envelope.origin.address)

    def _receive_transactions(self, envelope):
        """Handle transactions received"""
        # If node is miner store transactions in a pool (ordered by the gas price)
        transactions = envelope.msg.get('transactions')
        if self.is_mining:
            for tx in transactions:
                self.transaction_queue.put(tx)
        else:
            #TODO: validate_transaction('', tx)
            self.env.process(self.broadcast_transactions(transactions, None))

    def _receive_block_headers(self, envelope):
        """Handle block headers received"""
        block_headers = envelope.msg.get('block_headers')

        # TODO: Do not ask for a block body that is already in his blockchain

        # Save the header in a temporary list
        hashes = []
        for header in block_headers:
            self.temp_headers[header.hash] = header
            hashes.append(header.hash)
        self.request_bodies(hashes, envelope.origin.address)

    def _receive_block_bodies(self, envelope):
        """Handle block bodies received
        Assemble the block header in a temporary list with the block body received and
        insert it in the blockchain"""
        block_hashes = []
        block_bodies = envelope.msg.get('block_bodies')
        for block_hash, block_txs in block_bodies.items():
            block_hashes.append(block_hash[:4])
            if block_hash in self.temp_headers:
                header = self.temp_headers.get(block_hash)
                new_block = Block(header, block_txs)
                self.chain.add_block(new_block)
                del self.temp_headers[block_hash]
        print(
            f'{self.address} at {self.env.now}: {len(block_bodies)} Block(s) {block_hashes} assembled and added to the blockchain')

    def broadcast_new_blocks(self, new_blocks, upload_rate):
        """Specify one or more new blocks which have appeared on the network.
        To be maximally helpful, nodes should inform peers of all blocks that
        they may not be aware of."""
        new_blocks_hashes = {}
        for block in new_blocks:
            new_blocks_hashes[block.header.hash] = block.header.number

        new_blocks_msg = self.network_message.new_blocks(new_blocks_hashes)
        self.env.process(self.broadcast(upload_rate, new_blocks_msg))

    def _send_block_headers(self, envelope):
        """Send block headers for any node that request it, identified by the `destination_address`"""
        block_number = envelope.msg.get('block_number', 0)
        max_headers = envelope.msg.get('max_headers', 1)
        reverse = envelope.msg.get('reverse', 1)

        block_hash = self.chain.get_blockhash_by_number(block_number)
        block_hashes = self.chain.get_blockhashes_from_hash(
            block_hash, max_headers)

        block_headers = []
        for _block_hash in block_hashes:
            block_header = self.chain.get_block(_block_hash).header
            block_headers.append(block_header)
        if reverse == 0:
            block_headers.reverse()

        print(
            f'{self.address} at {self.env.now}: {len(block_headers)} Block header(s) preapred to send')

        block_headers_msg = self.network_message.block_headers(block_headers)
        self.env.process(
            self.send(envelope.origin.address, None, block_headers_msg))

    def _send_block_bodies(self, envelope):
        """Send block bodies for any node that request it, identified by the `destination_address`.

        In `envelope.msg.hashes` we obtain a list of hashes of block bodies being requested

        For now it only contains the transactions
        """
        block_bodies = {}
        for block_hash in envelope.msg.get('hashes'):
            block = self.chain.get_block(block_hash)
            block_bodies[block.header.hash] = block.transactions

        print(
            f'{self.address} at {self.env.now}: {len(block_bodies)} Block bodies(s) preapred to send')

        block_bodies_msg = self.network_message.block_bodies(block_bodies)
        self.env.process(
            self.send(envelope.origin.address, None, block_bodies_msg))

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
        get_headers_msg = self.network_message.get_headers(
            block_number, max_headers, reverse)
        self.env.process(
            self.send(destination_address, upload_rate, get_headers_msg))

    def request_bodies(self, hashes: list, destination_address: str, upload_rate=None):
        """Request a node (identified by the `destination_address`) to return block bodies.
        Specify a list of `hashes` that we're interested in.
        """
        get_block_bodies_msg = self.network_message.get_block_bodies(hashes)
        self.env.process(self.send(destination_address,
                                   upload_rate, get_block_bodies_msg))
