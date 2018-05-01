from blocksim.utils import encode_hex

default_config = dict(
    GENESIS_DIFFICULTY=1,
    GENESIS_PREVHASH=encode_hex(b'\x00' * 32),
    GENESIS_COINBASE=encode_hex(b'\x00' * 20),
    GENESIS_TIMESTAMP=0,
    GENESIS_NUMBER=0,
    BLANK_ROOT='00',
    BLOCK_SIZE=1
)
