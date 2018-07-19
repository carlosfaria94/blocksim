class Message:
    """Defines a model for the network messages of the Bitcoin blockchain.

    For each message its calculated the size, taking into account measurements from the live and public network.
    """

    def __init__(self, origin_node):
        self.origin_node = origin_node

    def inv(self, hashes, type: str):
        """Allows a node to advertise its knowledge of one or more transactions or blocks"""
        return {
            'id': 'inv',
            'type': type,
            'hashes': hashes,
            'size': 10  # TODO: Measure the size message
        }

    def tx(self, tx):
        """Sends a bitcoin transaction, in reply to getdata"""
        return {
            'id': 'tx',
            'tx': tx,
            'size': 10  # TODO: Measure the size message
        }

    def block(self, block):
        """Sends the body of a bitcoin block in response to a getdata message which requests transaction information from a block hash"""
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

    def get_headers(self, block_number: int, max_headers: int, reverse: int):
        """Requests a headers message that provides block headers starting from a particular point in the block chain"""
        return {
            'id': 'getheaders',
            'block_number': block_number,
            'max_headers': max_headers,
            'reverse': reverse,
            'size': 10  # TODO: Measure the size message
        }

    def headers(self, headers: list):
        """Sends block headers to a node which previously requested certain headers with a getheaders message"""
        return {
            'id': 'headers',
            'headers': headers,
            'size': 10  # TODO: Measure the size message
        }
