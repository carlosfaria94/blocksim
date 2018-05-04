from blocksim.utils import encode_hex

default_config = dict(
    GENESIS_DIFFICULTY=131072,
    GENESIS_GAS_LIMIT=3141592,
    GENESIS_PREVHASH=encode_hex(b'\x00' * 32),
    GENESIS_COINBASE=encode_hex(b'\x00' * 20),
    GENESIS_TIMESTAMP=0,
    GENESIS_NUMBER=0,
    BLANK_ROOT='681afa780d17da29203322b473d3f210a7d621259a4e6ce9e403f5a266ff719a',
    TX_BASE_GAS_COST=21000
)
