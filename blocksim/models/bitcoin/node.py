from blocksim.models.node import Node
from blocksim.models.network import Network
from blocksim.models.bitcoin.message import Message
from blocksim.models.chain import Chain
from blocksim.models.db import BaseDB
from blocksim.models.transaction_queue import TransactionQueue
from blocksim.models.block import Block, BlockHeader
from blocksim.models.bitcoin.config import default_config


class BTCNode(Node):
    def __init__(self,
                 env,
                 network: Network,
                 transmission_speed,
                 download_rate,
                 upload_rate,
                 location: str,
                 address: str,
                 is_mining=False):
        # Create the Bitcoin genesis block and init the chain
        genesis = Block(BlockHeader())
        chain = Chain(genesis, BaseDB())
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
        self.temp_txs = {}
        self.tx_on_transit = {}
        if is_mining:
            # Transaction Queue to store the transactions
            # TODO: The transaction queue delay is hard coded
            self.transaction_queue = TransactionQueue(env, 2, self)
            # TODO: The mining delays hard coded
            env.process(self.init_mining(2, 15, 3))
        self.network_message = Message(self)

    def init_mining(self,
                    duration_to_validate_tx,
                    duration_to_solve_puzzle,
                    block_size=default_config['BLOCK_SIZE']):
        """Simulates the mining operation.
        (1) Gets transactions from the queue
        (2) Validates each transaction (using the consensus model)
        (3) Constructs a candidate block with the valid transactions
        (4) Solves a cryptographic puzzle
        (5) Broadcast the candidate block with the Proof of Work (nonce)
        """
        print(
            f'{self.address} at {self.env.now}: Start mining process, waiting for transactions.')
        while True:
            txs_size = 0
            pending_txs = []
            while txs_size < block_size:
                pending_tx = yield self.transaction_queue.get()
                pending_txs.append(pending_tx)
                txs_size += pending_tx.size
                # Simulate the transaction validation
                yield self.env.timeout(duration_to_validate_tx)

            # Build the candidate block
            candidate_block = self._build_candidate_block(pending_txs)
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

    def _build_candidate_block(self, pending_txs):
        # Get the current head block
        prev_block = self.chain.head

        tx_list_root = default_config['BLANK_ROOT']
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
            difficulty,
            nonce)
        return Block(candidate_block_header, pending_txs)

    def _read_envelope(self, envelope):
        super()._read_envelope(envelope)
        if envelope.msg['id'] == 'inv':
            if envelope.msg['type'] == 'block':
                self._receive_new_blocks(envelope)
            if envelope.msg['type'] == 'tx':
                self._receive_new_transactions(envelope)
        if envelope.msg['id'] == 'getheaders':
            self._send_headers(envelope)
        if envelope.msg['id'] == 'headers':
            self._receive_headers(envelope)
        if envelope.msg['id'] == 'getdata':
            if envelope.msg['type'] == 'block':
                self._send_blocks(envelope)
            if envelope.msg['type'] == 'tx':
                self._send_transactions(envelope)
        if envelope.msg['id'] == 'block':
            self._receive_block(envelope)
        if envelope.msg['id'] == 'tx':
            self._receive_transaction(envelope)

    def _receive_transaction(self, envelope):
        """Handle full tx received"""
        transaction = envelope.msg.get('tx')
        del self.tx_on_transit[transaction.hash]
        # If node is miner store transactions in a pool
        if self.is_mining:
            self.transaction_queue.put(transaction)
        else:
            #TODO: validate_transaction('', tx)
            self.env.process(
                self.broadcast_transactions([transaction], None))

    def _receive_new_transactions(self, envelope):
        """Handle new transactions received"""
        request_txs = []
        for tx_hash in envelope.msg.get('hashes'):
            # Only request full TX that are not on transit
            if tx_hash not in self.tx_on_transit:
                request_txs.append(tx_hash)
        # Request the full TX
        if request_txs:
            self.request_txs(request_txs, envelope.origin.address)

    def _receive_new_blocks(self, envelope):
        """Handle new blocks received.
        The destination only receives the hash and number of the block. It is needed to
        ask for the header and body."""
        new_blocks = envelope.msg.get('hashes')
        print(f'{self.address} at {self.env.now}: New blocks received {new_blocks}')
        # TODO: hash_stop - we can send the hash tip of the node requesting the headers
        # TODO: This need to be improved, we need send all the hashes?
        self.request_headers(new_blocks[0], '', envelope.origin.address)

    def broadcast_new_blocks(self, new_blocks, upload_rate):
        """Specify one or more new blocks which have appeared on the network."""
        new_blocks_hashes = []
        for block in new_blocks:
            new_blocks_hashes.append(block.header.hash)

        new_blocks_msg = self.network_message.inv(new_blocks_hashes, 'block')
        self.env.process(self.broadcast(upload_rate, new_blocks_msg))

    def broadcast_transactions(self, transactions: list, upload_rate):
        """Broadcast transactions to all nodes with an active session and mark the hashes
        as known by each node"""
        yield self.connecting  # Wait for all connections
        for node_address, node in self.active_sessions.items():
            transactions_hashes = []
            for tx in transactions:
                # Add the transaction to a temporary list
                self.temp_txs[tx.hash] = tx
                # Checks if the transaction was previous sent
                if any({tx.hash} & node.get('knownTxs')):
                    print(
                        f'{self.address} at {self.env.now}: Transaction {tx.hash[:8]} was already sent to {node_address}')
                else:
                    self._mark_transaction(tx.hash, node_address)
                    transactions_hashes.append(tx.hash)

        # Only send if it has transactions hashes
        if transactions_hashes:
            print(
                f'{self.address} at {self.env.now}: {len(transactions_hashes)} transaction(s) ready to be announced')
            transactions_msg = self.network_message.inv(
                transactions_hashes, 'tx')

            self.env.process(self.broadcast(upload_rate, transactions_msg))

    def _receive_block(self, envelope):
        """Handle block bodies received
        Assemble the block header in a temporary list with the block body received and
        insert it in the blockchain"""
        block = envelope.msg.get('block')
        if block.header.hash in self.temp_headers:
            header = self.temp_headers.get(block.header.hash)
            new_block = Block(header, block.transactions)
            self.chain.add_block(new_block)
            del self.temp_headers[block.header.hash]
            print(
                f'{self.address} at {self.env.now}: Block {new_block.header.hash[:8]} assembled and added to the blockchain')

    def _send_transactions(self, envelope):
        """Send a full transaction for any node that request it, identified by the
        `destination_address`. In `request['hashes']` we obtain a list of hashes of
        block bodies being requested
        """
        for tx_hash in envelope.msg.get('hashes'):
            if tx_hash in self.temp_txs:
                tx = self.temp_txs.get(tx_hash)
                del self.temp_txs[tx_hash]

                print(
                    f'{self.address} at {self.env.now}: Full transaction {tx.hash[:8]} preapred to send')

                tx_msg = self.network_message.tx(tx)
                self.env.process(
                    self.send(envelope.origin.address, None, tx_msg))

    def _send_blocks(self, envelope):
        """Send the block for any node that request it, identified by the `destination_address`.
        In `request['hashes']` we obtain a list of hashes of block bodies being requested
        """
        for block_hash in envelope.msg.get('hashes'):
            block = self.chain.get_block(block_hash)

            print(
                f'{self.address} at {self.env.now}: Block {block.header.hash[:8]} preapred to send')

            block_bodies_msg = self.network_message.block(block)
            self.env.process(
                self.send(envelope.origin.address, None, block_bodies_msg))

    def request_bodies(self, hashes: list, destination_address: str, upload_rate=None):
        get_data_msg = self.network_message.get_data(hashes, 'block')
        self.env.process(
            self.send(destination_address, upload_rate, get_data_msg))

    def request_txs(self, hashes: list, destination_address: str, upload_rate=None):
        # Mark transaction on transit
        for tx_hash in hashes:
            self.tx_on_transit[tx_hash] = tx_hash
        get_data_msg = self.network_message.get_data(hashes, 'tx')
        self.env.process(
            self.send(destination_address, upload_rate, get_data_msg))

    def _receive_headers(self, envelope):
        """Handle block headers received.
        Receive the headers, validate the headers, save on a temporary list and then
        ask for the bodies of the block"""
        block_headers = envelope.msg.get('headers')
        # Save the header in a temporary list
        hashes = []
        for header in block_headers:
            # TODO: Validate the header, if not valid, do not request it
            self.temp_headers[header.hash] = header
            hashes.append(header.hash)
        self.request_bodies(hashes, envelope.origin.address)

    def _send_headers(self, envelope):
        """Send block headers for any node that request it, identified by the `destination_address`"""
        block_locator_hash = envelope.msg.get('block_locator_hash')
        hash_stop = envelope.msg.get('hash_stop')  # TODO: Use hash_stop
        MAX_HEADERS = 2000  # Max number of headers

        block_hashes = self.chain.get_blockhashes_from_hash(
            block_locator_hash, MAX_HEADERS)

        block_headers = []
        for _block_hash in block_hashes:
            block_header = self.chain.get_block(_block_hash).header
            block_headers.append(block_header)

        print(
            f'{self.address} at {self.env.now}: {len(block_headers)} Block header(s) preapred to send')

        headers_msg = self.network_message.headers(block_headers)
        self.env.process(
            self.send(envelope.origin.address, None, headers_msg))

    def request_headers(self,
                        block_locator_hash: str,
                        hash_stop: str,
                        destination_address: str,
                        upload_rate=None):
        get_headers_msg = self.network_message.get_headers(
            block_locator_hash, hash_stop)
        self.env.process(
            self.send(destination_address, upload_rate, get_headers_msg))
