import binascii
from datetime import datetime
import random
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


def get_latency_delay(env, origin: str, destination: str, n=1):
    distribution = env.delays['LATENCIES'][origin][destination]
    # Convert latency in ms to seconds
    latencies = [
        latency/1000 for latency in get_random_values(distribution, n)]
    if len(latencies) == 1:
        return round(latencies[0], 4)
    else:
        return latencies


def get_received_delay(env, message_size: float, origin: str, destination: str, n=1):
    """
    It calculates and returns a delay when receiving/downloading a message with a certain size (`message_size`)

    :param message_size: message size in megabytes (MB)
    :param origin: the location of the origin node
    :param destination: the location of the destination node
    :param n: the number of delays returned

    If `n` is 1 it returns a `float`, if `n > 1` returns an array of `n` floats.
    """
    distribution = env.delays['THROUGHPUT_RECEIVED'][origin][destination]
    delay = _calc_throughput(distribution, message_size, n)
    if delay < 0:
        raise RuntimeError(
            f'Negative received delay ({delay}) to origin {origin} and destination {destination}')
    else:
        return delay


def get_sent_delay(env, message_size: float, origin: str, destination: str, n=1):
    """
    It calculates and returns a delay when sending/uploading a message with a certain size (`message_size`)

    :param message_size: message size in megabytes (MB)
    :param origin: the location of the origin node
    :param destination: the location of the destination node
    :param n: the number of delays returned

    If `n` is 1 it returns a `float`, if `n > 1` returns an array of `n` floats.
    """
    distribution = env.delays['THROUGHPUT_SENT'][origin][destination]
    delay = _calc_throughput(distribution, message_size, n)
    if delay < 0:
        raise RuntimeError(
            f'Negative sent delay ({delay}) to origin {origin} and destination {destination}')
    else:
        return delay


def _calc_throughput(distribution: dict, message_size: float, n):
    rand_throughputs = get_random_values(distribution, n)
    delays = []
    for throughput in rand_throughputs:
        delay = (message_size * 8) / throughput
        delays.append(delay)
    if len(delays) == 1:
        return round(delays[0], 3)
    else:
        return delays


def time(env):
    return datetime.utcfromtimestamp(env.now).strftime('%m-%d %H:%M:%S')


def kB_to_MB(value):
    return value / 1000


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
