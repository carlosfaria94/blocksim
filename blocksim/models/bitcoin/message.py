class Message:
    """Defines a model for the network messages of the Bitcoin blockchain.

    For each message its calculated the size, taking into account measurements from the live and public network.
    """

    def __init__(self, origin_node):
        self.origin_node = origin_node

    def version(self):
        return {
            'id': 'version',
            'size': 1
        }

    def verack(self):
        return {
            'id': 'verack',
            'size': 1
        }

    def inv(self, hashes: list, _type: str):
        """Allows a node to advertise its knowledge of one or more transactions or blocks"""
        return {
            'id': 'inv',
            'type': _type,
            'hashes': hashes,
            'size': 1
        }

    def tx(self, tx):
        """Sends a bitcoin transaction, in reply to getdata"""
        return {
            'id': 'tx',
            'tx': tx,
            'size': 1
        }

    def block(self, block):
        """Sends the body of a bitcoin block in response to a getdata message which requests transaction information from a block hash"""
        return {
            'id': 'block',
            'block': block,
            'size': 1
        }

    def get_data(self, hashes: list, _type: str):
        """Used to retrieve the content of a specific type (e.g. block or transaction).
        It can be used to retrieve transactions or blocks"""
        return {
            'id': 'getdata',
            'type': _type,
            'hashes': hashes,
            'size': 1
        }

    def get_headers(self, block_number: int, max_headers: int, reverse: int):
        """Requests a headers message that provides block headers starting from a particular point in the block chain"""
        return {
            'id': 'getheaders',
            'block_number': block_number,
            'max_headers': max_headers,
            'reverse': reverse,
            'size': 1
        }

    def headers(self, headers: list):
        """Sends block headers to a node which previously requested certain headers with a getheaders message"""
        return {
            'id': 'headers',
            'headers': headers,
            'size': 1
        }
