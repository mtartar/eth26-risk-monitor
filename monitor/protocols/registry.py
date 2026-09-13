"""Registry mapping a protocol/chain key to its config and risk model.

This is the seam that makes the system generic: adding a new protocol/chain
pair means writing one new module (like aave_v2_ethereum.py) and adding two
entries here — no other code should need to change.

aave-v3-ethereum is deliberately not registered yet: no verified Substreams
package exists for it (see docs/phase1_findings.md). Registering a config
with no real data source behind it would let code silently "succeed" against
nothing — better to fail an unknown-key lookup than a real risk-monitoring
system that quietly monitors nothing.
"""

from monitor.protocols.aave_v2_ethereum import AAVE_V2_ETHEREUM, AaveV2RiskModel
from monitor.protocols.models import ProtocolConfig, RiskModel

PROTOCOL_CONFIGS: dict[str, ProtocolConfig] = {
    "aave-v2-ethereum": AAVE_V2_ETHEREUM,
}

RISK_MODELS: dict[str, RiskModel] = {
    "aave-v2-ethereum": AaveV2RiskModel(),
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
