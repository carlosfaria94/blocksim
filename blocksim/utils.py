import binascii
try:
    from Crypto.Hash import keccak

    def keccak_256(value):
        return keccak.new(digest_bits=256, data=value).digest()
except ImportError:
    import sha3 as _sha3

    def keccak_256(value):
        return _sha3.keccak_256(value).digest()
from py_ecc.secp256k1 import privtopub, ecdsa_raw_sign

TT256 = 2 ** 256

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

def is_numeric(x):
    return isinstance(x, int)

def encode_int32(v):
    return v.to_bytes(32, byteorder='big')

def normalize_key(key):
    if is_numeric(key):
        o = encode_int32(key)
    elif len(key) == 32:
        o = key
    elif len(key) == 64:
        o = decode_hex(key)
    elif len(key) == 66 and key[:2] == '0x':
        o = decode_hex(key[2:])
    else:
        raise Exception("Invalid key format: %r" % key)
    if o == b'\x00' * 32:
        raise Exception("Zero privkey invalid")
    return o

def ecsign(rawhash, key):
    v, r, s = ecdsa_raw_sign(rawhash, key)
    return v, r, s

def privtoaddr(k):
    k = normalize_key(k)
    x, y = privtopub(k)
    return keccak_256(encode_int32(x) + encode_int32(y))[12:]
