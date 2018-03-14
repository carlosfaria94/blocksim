from blocksim.utils import TT256, keccak_256, encode_hex
from blocksim.exceptions import InvalidTransaction

# in the yellow paper it is specified that s should be smaller than
# secpk1n (eq.205)
secpk1n = 115792089237316195423570985008687907852837564279074904382605163141518161494337
null_address = b'\xff' * 20

class Transaction:
    """ Defines the transaction model.

    In Ethereum a transaction is stored as:
    :param int nonce: sequence number, issued by the originating EOA, used to prevent message replay
    :param gasprice: price of gas (in wei) the originator is willing to pay
    :param startgas: maximum amount of gas the originator is willing to pay
    :param to: destination Ethereum address
    :param value: amount of ether to send to destination
    :param data: variable length binary data payload

    The three components of an ECDSA signature of the originating EOA:
    :param v: chain identifier (EIP-155 "Simple Replay Attack Protection")
    :param r
    :param s

    """

    _sender = None

    def __init__(self, nonce, gasprice, startgas, to, value, data, v=0, r=0, s=0):
        self.nonce = nonce
        self.gasprice = gasprice
        self.startgas = startgas
        self.to = to
        self.value = value
        self.data = data
        self.v = v
        self.r = r
        self.s = s

        if self.gasprice >= TT256 or self.startgas >= TT256 or \
                self.value >= TT256 or self.nonce >= TT256:
            raise InvalidTransaction("Values way too high!")

    @property
    def network_id(self):
        if self.r == 0 and self.s == 0:
            return self.v
        elif self.v in (27, 28):
            return None
        else:
            return ((self.v - 1) // 2) - 17

    @property
    def sender(self):
        if not self._sender:
            print('Sender not set')
            # Determine sender
            # TODO: https://github.com/ethereum/pyethereum/blob/develop/ethereum/transactions.py#L80
        return self._sender

    @sender.setter
    def sender(self, value):
        self._sender = value

    @property
    def hash(self):
        """The transaction hash"""
        return encode_hex(keccak_256(str(self).encode('utf-8')))

    def __repr__(self):
        """Returns a unambiguous representation of the transaction"""
        return f'<{self.__class__.__name__}({self.hash})>'

    def __str__(self):
        """Returns a readable representation of the transaction"""
        return f'''<{self.__class__.__name__}(nonce:{self.nonce} gasprice:{self.gasprice} startgas:{self.startgas} to:{self.to} value:{self.value} data:{self.data} v:{self.v} r:{self.r} s:{self.s})>'''

    def __eq__(self, other):
        """Two transactions are equal iff they have the same hash."""
        return isinstance(other, self.__class__) and self.hash == other.hash

    def __lt__(self, other):
        return isinstance(other, self.__class__) and self.hash < other.hash

    def __ne__(self, other):
        return not self.__eq__(other)
