from blocksim.utils import keccak_256, encode_hex


class Transaction:
    """ Defines a basic transaction model.

    We can define a simple and basic model of a transaction by defining the following
    parameters:

    :param to: destination address
    :param sender: sender address
    :param value: amount to send to destination
    :param signature: sender signature
    :param fee: a fee destinated to the node that will insert the transaction on the chain
    """

    def __init__(self,
                 to,
                 sender,
                 value,
                 signature,
                 fee):
        self.to = to
        self.sender = sender
        self.value = value
        self.signature = signature
        self.fee = fee

    @property
    def hash(self):
        """The transaction hash using Keccak 256"""
        return encode_hex(keccak_256(str(self).encode('utf-8')))

    def __repr__(self):
        """Returns a unambiguous representation of the transaction"""
        return f'<{self.__class__.__name__}({self.hash})>'

    def __str__(self):
        """Returns a readable representation of the transaction"""
        return f'''<{self.__class__.__name__}(to:{self.to} sender:{self.sender} value:{self.value} signature:{self.signature} fee:{self.fee})>'''

    def __eq__(self, other):
        """Two transactions are equal iff they have the same hash."""
        return isinstance(other, self.__class__) and self.hash == other.hash

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return isinstance(other, self.__class__) and self.fee < other.fee

    def __le__(self, other):
        return isinstance(other, self.__class__) and self.fee <= other.fee

    def __gt__(self, other):
        return isinstance(other, self.__class__) and self.fee > other.fee

    def __ge__(self, other):
        return isinstance(other, self.__class__) and self.fee >= other.fee
