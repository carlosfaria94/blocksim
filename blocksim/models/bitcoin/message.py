class Message:
    """Defines a model for the network messages of the Bitcoin blockchain.

    For each message its calculated the size, taking into account measurements from the live and public network.
    """

    def __init__(self, origin_node):
        self.origin_node = origin_node

    def inv(self, hashes: list, type: str):
        """Allows a node to advertise its knowledge of one or more transactions or blocks"""
        return {
            'id': 'inv',
            'type': type,
            'hashes': hashes,
            'size': 10  # TODO: Measure the size message
        }

    def tx(self, tx):
        return {
            'id': 'tx',
            'tx': tx,
            'size': 10  # TODO: Measure the size message
        }

    def block(self, block):
        return {
            'id': 'block',
            'block': block,
            'size': 10  # TODO: Measure the size message
        }

    def get_data(self, hashes: list, type: str):
        """Used to retrieve the content of a specific type (e.g. block or transaction).
        It can be used to retrieve transactions or blocks"""
        return {
            'id': 'getdata',
            'type': type,
            'hashes': hashes,
            'size': 10  # TODO: Measure the size message
        }

    def get_headers(self, block_locator_hash: str, hash_stop: str):
        return {
            'id': 'getheaders',
            'block_locator_hash': block_locator_hash,
            'hash_stop': hash_stop,
            'size': 10  # TODO: Measure the size message
        }

    def headers(self, headers: list):
        """ Reply to `get_headers` the items in the list are block headers.
        """
        return {
            'id': 'headers',
            'headers': headers,
            'size': 10  # TODO: Measure the size message
        }
