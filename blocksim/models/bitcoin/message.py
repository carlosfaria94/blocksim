from blocksim.utils import kB_to_MB


class Message:
    """Defines a model for the network messages of the Bitcoin blockchain.

    For each message its calculated the size, taking into account measurements from the live and public network.
    """

    def __init__(self, origin_node):
        self._origin_node = origin_node
        _env = origin_node.env
        self._message_size = _env.config['bitcoin']['message_size_kB']
        # In bitcoin the header size has a fixed size https://en.bitcoin.it/wiki/Protocol_documentation#Message_structure
        self._header_size = self._message_size['header']

    def version(self):
        """ When a node creates an outgoing connection, it will immediately advertise its version.
        https://en.bitcoin.it/wiki/Protocol_documentation#version"""
        return {
            'id': 'version',
            'size': kB_to_MB(self._header_size + self._message_size['version'])
        }

    def verack(self):
        """ The verack message is sent in reply to version. This message consists of only
        a message header with the command string "verack".
        https://en.bitcoin.it/wiki/Protocol_documentation#verack"""
        return {
            'id': 'verack',
            'size': kB_to_MB(self._header_size + self._message_size['verack'])
        }

    def inv(self, hashes: list, _type: str):
        """Allows a node to advertise its knowledge of one or more transactions or blocks
        https://en.bitcoin.it/wiki/Protocol_documentation#inv"""
        num_items = len(hashes)
        inv_size = num_items * self._message_size['inv_vector']
        return {
            'id': 'inv',
            'type': _type,
            'hashes': hashes,
            'size': kB_to_MB(self._header_size + inv_size)
        }

    def tx(self, tx):
        """Sends a bitcoin transaction, in reply to getdata
        https://en.bitcoin.it/wiki/Protocol_documentation#tx"""
        return {
            'id': 'tx',
            'tx': tx,
            'size': kB_to_MB(self._header_size + self._message_size['tx'])
        }

    def block(self, block):
        """Sends the body of a bitcoin block in response to a getdata message which
        requests transaction information from a block hash
        https://en.bitcoin.it/wiki/Protocol_documentation#block"""
        num_txs_block = len(block.transactions)
        block_txs_size = self._message_size['tx'] * num_txs_block
        total_block_size = self._header_size + \
            self._message_size['block_base'] + block_txs_size
        return {
            'id': 'block',
            'block': block,
            'size': kB_to_MB(total_block_size)
        }

    def get_data(self, hashes: list, _type: str):
        """Used to retrieve the content of a specific type (e.g. block or transaction).
        It can be used to retrieve transactions or blocks
        https://en.bitcoin.it/wiki/Protocol_documentation#getdata"""
        num_items = len(hashes)
        inv_size = num_items * self._message_size['inv_vector']
        return {
            'id': 'getdata',
            'type': _type,
            'hashes': hashes,
            'size': kB_to_MB(self._header_size + inv_size)
        }
