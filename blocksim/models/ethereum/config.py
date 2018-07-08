from blocksim.models.config import default_config

ethereum_config = dict(
    GENESIS_GAS_LIMIT=3141592,
    TX_BASE_GAS_COST=21000
)

default_config.update(ethereum_config)
