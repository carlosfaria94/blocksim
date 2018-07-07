import random
import simpy
from blocksim.models.node import Node
from blocksim.models.network import Network
from blocksim.models.bitcoin.message import Message
from blocksim.models.chain import Chain
from blocksim.models.db import BaseDB
from blocksim.models.consensus import Consensus
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
        self.consensus = Consensus(env)
        chain = Chain(env, self, self.consensus, genesis, BaseDB())
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
        self.network_message = Message(self)
        if is_mining:
            # Transaction Queue to store the transactions
            self.transaction_queue = TransactionQueue(env, self)
            self.mining_current_block = None
            env.process(self._init_mining())

    def _init_mining(self):
        """Simulates the mining operation.
        (1) Gets transactions from the queue
        (2) Constructs a candidate block with the valid transactions
        (3) Solves a cryptographic puzzle
        (4) Broadcast the candidate block with the Proof of Work (nonce)
        (5) Adds the block to the chain
        """
        if self.is_mining is False:
            raise RuntimeError(f'Node {self.location} is not a miner')

        print(
            f'{self.address} at {self.env.now}: Start mining process, waiting for transactions.')

        block_size = default_config['BLOCK_SIZE']
        txs_size = 0
        pending_txs = []
        while txs_size < block_size:
            pending_tx = yield self.transaction_queue.get()
            pending_txs.append(pending_tx)
            txs_size += pending_tx.size

        # Build the candidate block
        candidate_block = self._build_candidate_block(pending_txs)
        print(
            f'{self.address} at {self.env.now}: New candidate block created {candidate_block.header.hash[:8]}')

        # Mine the block by simulating the resolution of a puzzle
        self.mining_current_block = self.env.process(
            self._mine(candidate_block))

    def _mine(self, candidate_block):
        """Simulates the mining operation.
        Change the nonce to 'MINED' to mark block as mined.
        In a simulation it is not needed to compute the real nonce"""
        try:
            while True:
                candidate_block.header.nonce = 'MINED'
                # A mining process will be delayed according to a normal distribution previously measured
                yield self.env.timeout(self.env.delays['time_between_blocks'])
                # But, finding the solution to the cryptographic puzzle can be random as flipping a coin
                solved_puzzle = bool(random.getrandbits(1))
                if solved_puzzle is True:
                    print(
                        f'{self.address} at {self.env.now}: Solved the cryptographic puzzle for the candidate block {candidate_block.header.hash[:8]}')

                    # We need to broadcast the new candidate block across the network
                    self.broadcast_new_blocks([candidate_block], None)

                    # Add the candidate block to the chain of the miner node
                    self.chain.add_block(candidate_block)
                    break
                else:
                    print(
                        f'{self.address} at {self.env.now}: Cannot solve cryptographic puzzle for the candidate block. Try again.')
        except simpy.Interrupt as i:
            # The mining of the current block has interrupted
            # Probably a new block has founded, forget this block, and start mining a new one.
            print(
                f'{self.address} at {self.env.now}: Stop mining current candidate block and start mining a new one')
            self._init_mining()

    def _build_candidate_block(self, pending_txs):
        # Get the current head block
        prev_block = self.chain.head
        tx_list_root = default_config['BLANK_ROOT']
        timestamp = self.env.now
        difficulty = self.consensus.calc_difficulty(prev_block, timestamp)
        nonce = ''
        block_number = prev_block.header.number + 1
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
        The destination only receives the hash and number of the block. It is needed
        to ask for the header and body."""
        if self.is_mining and self.mining_current_block.is_alive:
            self.mining_current_block.interrupt()
        new_blocks = envelope.msg.get('hashes')
        print(f'{self.address} at {self.env.now}: New blocks received {new_blocks}')
        # If the block is already known by a node, it does not need to request the block again
        block_numbers = []
        for block_hash, block_number in new_blocks.items():
            if self.chain.get_block(block_hash) is None:
                block_numbers.append(block_number)
        lowest_block_number = min(block_numbers)
        self.request_headers(
            lowest_block_number, len(new_blocks), 0, envelope.origin.address)

    def broadcast_new_blocks(self, new_blocks, upload_rate):
        """Specify one or more new blocks which have appeared on the network."""
        new_blocks_hashes = {}
        for block in new_blocks:
            new_blocks_hashes[block.header.hash] = block.header.number

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
        inserted into the blockchain"""
        block = envelope.msg.get('block')
        if block.header.hash in self.temp_headers:
            header = self.temp_headers.get(block.header.hash)
            new_block = Block(header, block.transactions)
            if self.chain.add_block(new_block):
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
            self.temp_headers[header.hash] = header
            hashes.append(header.hash)
        self.request_bodies(hashes, envelope.origin.address)

    def _send_headers(self, envelope):
        """Send block headers for any node that request it, identified by the `destination_address`"""
        block_number = envelope.msg.get('block_number', 0)
        max_headers = envelope.msg.get('max_headers', 1)
        reverse = envelope.msg.get('reverse', 1)

        # In bitcoin we can only send a maximum of 20000 block headers
        if max_headers > 2000:
            max_headers = 2000

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

        headers_msg = self.network_message.headers(block_headers)
        self.env.process(
            self.send(envelope.origin.address, None, headers_msg))

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
