"""Registry mapping a protocol/chain key to its config and risk model.

This is the seam that makes the system generic: adding a new protocol/chain
pair means writing one new module (like aave_v3_ethereum.py) and adding two
entries here — no other code should need to change.
"""

from monitor.protocols.aave_v3_ethereum import AAVE_V3_ETHEREUM, AaveV3RiskModel
from monitor.protocols.models import ProtocolConfig, RiskModel

PROTOCOL_CONFIGS: dict[str, ProtocolConfig] = {
    "aave-v3-ethereum": AAVE_V3_ETHEREUM,
}

RISK_MODELS: dict[str, RiskModel] = {
    "aave-v3-ethereum": AaveV3RiskModel(),
}


def get_protocol_config(key: str) -> ProtocolConfig:
    """Look up a protocol/chain config by its registry key."""
    if key not in PROTOCOL_CONFIGS:
        raise KeyError(f"Unknown protocol/chain '{key}'. Known: {sorted(PROTOCOL_CONFIGS)}")
    return PROTOCOL_CONFIGS[key]


def get_risk_model(key: str) -> RiskModel:
    """Look up a protocol/chain's risk model by its registry key."""
    if key not in RISK_MODELS:
        raise KeyError(f"Unknown protocol/chain '{key}'. Known: {sorted(RISK_MODELS)}")
    return RISK_MODELS[key]
