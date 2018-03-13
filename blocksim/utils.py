import binascii
try:
    from Crypto.Hash import keccak

    def keccak_256(value):
        return keccak.new(digest_bits=256, data=value).digest()
except ImportError:
    import sha3 as _sha3

    def keccak_256(value):
        return _sha3.keccak_256(value).digest()

def decode_hex(s):
    if isinstance(s, str):
        return bytes.fromhex(s)
    if isinstance(s, (bytes, bytearray)):
        return binascii.unhexlify(s)
    raise TypeError('Value must be an instance of str or bytes')


def encode_hex(b):
    if isinstance(b, str):
        b = bytes(b, 'utf-8')
    if isinstance(b, (bytes, bytearray)):
        return str(binascii.hexlify(b), 'utf-8')
    raise TypeError('Value must be an instance of str or bytes')
