import binascii
from ast import literal_eval as make_tuple
import scipy.stats
try:
    from Crypto.Hash import keccak

    def keccak_256(value):
        return keccak.new(digest_bits=256, data=value).digest()
except ImportError:
    import sha3 as _sha3

    def keccak_256(value):
        return _sha3.keccak_256(value).digest()


def get_transmission_delay(env, message_size: float, isDownload: bool, origin: str, destination: str, n=1):
    """
    message_size: float message size in megabits (MB)

    """
    if isDownload is True:
        location = env.delays['DOWNLOAD_BANDWIDTH'][origin][destination]
    else:
        location = env.delays['UPLOAD_BANDWIDTH'][origin][destination]
    dist = getattr(scipy.stats, location['name'])
    param = make_tuple(location['parameters'])
    rand_bandwidths = dist.rvs(
        *param[:-2], loc=param[-2], scale=param[-1], size=n)
    throughputs = []
    for bandwidth in rand_bandwidths:
        # if effective <= 0 or effective >= 1:
        #    raise RuntimeError(
        #        'Invalid effective throughput. It needs to be in the interval ]0, 1[')
        throughput = (message_size * 8) / bandwidth
        throughputs.append(throughput)
    if len(throughputs) == 1:
        return round(throughputs[0], 3)
    else:
        return throughputs


def get_random_values(distribution: dict, n=1):
    """Receives a `distribution` and outputs `n` random values
    Distribution format: { \'name\': str, \'parameters\': tuple }"""
    dist = getattr(scipy.stats, distribution['name'])
    param = make_tuple(distribution['parameters'])
    return dist.rvs(*param[:-2], loc=param[-2], scale=param[-1], size=n)


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
