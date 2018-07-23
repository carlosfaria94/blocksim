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
from blocksim.models.config import default_config
from blocksim.utils import get_random_values


class BTCNode(Node):
    def __init__(self,
                 env,
                 network: Network,
                 location: str,
                 address: str,
                 is_mining=False):
        # Create the Bitcoin genesis block and init the chain
        genesis = Block(BlockHeader())
        self.consensus = Consensus(env)
        chain = Chain(env, self, self.consensus, genesis, BaseDB())
        super().__init__(env,
                         network,
                         location,
                         address,
                         chain)
        self.is_mining = is_mining
        self.config = default_config
        self.temp_txs = {}
        self.tx_on_transit = {}
        self.network_message = Message(self)
        if is_mining:
            # Transaction Queue to store the transactions
            self.transaction_queue = TransactionQueue(
                env, self, self.consensus)
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

        block_size = self.config['BLOCK_SIZE_LIMIT']
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
                yield self.env.timeout(2)
                # But, finding the solution to the cryptographic puzzle can be random as flipping a coin
                solved_puzzle = bool(random.getrandbits(1))
                if solved_puzzle is True:
                    print(
                        f'{self.address} at {self.env.now}: Solved the cryptographic puzzle for the candidate block {candidate_block.header.hash[:8]}')

                    # We need to broadcast the new candidate block across the network
                    self.broadcast_new_blocks([candidate_block])

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
        coinbase = self.address
        timestamp = self.env.now
        difficulty = self.consensus.calc_difficulty(prev_block, timestamp)
        block_number = prev_block.header.number + 1
        candidate_block_header = BlockHeader(
            prev_block.header.hash,
            block_number,
            timestamp,
            coinbase,
            difficulty)
        return Block(candidate_block_header, pending_txs)

    def _read_envelope(self, envelope):
        """It implements how bitcon P2P protocol works, more info here:
        https://bitcoin.org/en/developer-reference#p2p-network"""
        super()._read_envelope(envelope)
        if envelope.msg['id'] == 'inv':
            if envelope.msg['type'] == 'block':
                self._receive_new_inv_blocks(envelope)
            if envelope.msg['type'] == 'tx':
                self._receive_new_inv_transactions(envelope)
        if envelope.msg['id'] == 'getdata':
            if envelope.msg['type'] == 'block':
                self._send_full_blocks(envelope)
            if envelope.msg['type'] == 'tx':
                self._send_full_transactions(envelope)
        if envelope.msg['id'] == 'block':
            self._receive_full_block(envelope)
        if envelope.msg['id'] == 'tx':
            self._receive_full_transaction(envelope)

    ##              ##
    ## Transactions ##
    ##              ##

    def request_txs(self, hashes: list, destination_address: str):
        """Request transactions to a specific node by `destination_address`"""
        for tx_hash in hashes:
            self.tx_on_transit[tx_hash] = tx_hash
        get_data_msg = self.network_message.get_data(hashes, 'tx')
        self.env.process(self.send(destination_address, None, get_data_msg))

    def broadcast_transactions(self, transactions: list):
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
                    # Calculates the delay to validate the tx
                    tx_validation_delay = self.consensus.validate_transaction()
                    yield self.env.timeout(tx_validation_delay)
                    self._mark_transaction(tx.hash, node_address)
                    transactions_hashes.append(tx.hash)
        # Only send if it has transactions hashes
        if transactions_hashes:
            print(
                f'{self.address} at {self.env.now}: {len(transactions_hashes)} transaction(s) ready to be announced')
            transactions_msg = self.network_message.inv(
                transactions_hashes, 'tx')
            self.env.process(self.broadcast(None, transactions_msg))

    def _send_full_transactions(self, envelope):
        """Send a full transaction for any node that request it, identified by the
        `destination_address`. In `envelope.msg['hashes']` we obtain a list of hashes of
        transactions being requested
        """
        for tx_hash in envelope.msg['hashes']:
            if tx_hash in self.temp_txs:
                tx = self.temp_txs[tx_hash]
                del self.temp_txs[tx_hash]
                print(
                    f'{self.address} at {self.env.now}: Full transaction {tx.hash[:8]} preapred to send')
                tx_msg = self.network_message.tx(tx)
                self.env.process(
                    self.send(envelope.origin.address, None, tx_msg))

    def _receive_new_inv_transactions(self, envelope):
        """Handle new transactions received"""
        request_txs = []
        for tx_hash in envelope.msg.get('hashes'):
            # Only request full TX that are not on transit
            if tx_hash not in self.tx_on_transit:
                request_txs.append(tx_hash)
        # Request the full TX
        if request_txs:
            self.request_txs(request_txs, envelope.origin.address)

    def _receive_full_transaction(self, envelope):
        """Handle full tx received"""
        transaction = envelope.msg.get('tx')
        del self.tx_on_transit[transaction.hash]
        # If node is miner store transactions in a pool
        if self.is_mining:
            self.transaction_queue.put(transaction)
        else:
            self.env.process(
                self.broadcast_transactions([transaction]))

    ##              ##
    ## Blocks       ##
    ##              ##

    def broadcast_new_blocks(self, new_blocks: list):
        """Specify one or more new blocks which have appeared on the network."""
        new_blocks_hashes = [b.header.hash for b in new_blocks]
        new_blocks_msg = self.network_message.inv(new_blocks_hashes, 'block')
        self.env.process(self.broadcast(None, new_blocks_msg))

    def _receive_new_inv_blocks(self, envelope):
        """Handle new `inv` blocks received (https://bitcoin.org/en/developer-reference#inv).
        The destination only receives the hash of the block, and then ask for the entire block
        by calling `getdata` netowork protocol message (https://bitcoin.org/en/developer-reference#getdata)."""
        if self.is_mining:
            if self.mining_current_block and self.mining_current_block.is_alive:
                self.mining_current_block.interrupt()
        new_blocks_hashes = envelope.msg.get('hashes')
        print(
            f'{self.address} at {self.env.now}: {len(new_blocks_hashes)} new blocks announced by {envelope.origin.address}')
        get_data_msg = self.network_message.get_data(
            new_blocks_hashes, 'block')
        self.env.process(
            self.send(envelope.origin.address, None, get_data_msg))

    def _receive_full_block(self, envelope):
        """Handle full blocks received.
        The node tries to add the block to the chain, by performing validation."""
        block = envelope.msg['block']
        is_added = self.chain.add_block(block)
        if is_added:
            print(
                f'{self.address} at {self.env.now}: Block assembled and added to the tip of the chain {block.header}')
        else:
            print(
                f'{self.address} at {self.env.now}: Block NOT added to the chain {block.header}')

        # TODO: Delete next lines. We need to have another way to see the final state of the chain for each node
        head = self.chain.head
        print(
            f'{self.address} at {self.env.now}: head {head.header.hash[:8]} #{head.header.number} {head.header.difficulty}')
        for i in range(head.header.number):
            b = self.chain.get_block_by_number(i)
            print(
                f'{self.address} at {self.env.now}: block {b.header.hash[:8]} #{b.header.number} {b.header.difficulty}')

    def _send_full_blocks(self, envelope):
        """Send a full block (https://bitcoin.org/en/developer-reference#block) for any node that
        request it (`envelope.origin.address`) by using `getdata`.
        In `envelope.msg['hashes']` we obtain a list of hashes of full blocks being requested
        """
        origin = envelope.origin.address
        for block_hash in envelope.msg['hashes']:
            block = self.chain.get_block(block_hash)
            print(
                f'{self.address} at {self.env.now}: Block {block.header.hash[:8]} preapred to send to {origin}')
            block_msg = self.network_message.block(block)
            self.env.process(self.send(origin, None, block_msg))
